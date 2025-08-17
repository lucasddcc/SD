# servidor_lider.py
import socket
import threading
from tarefas import ListaTarefas
from mensagens import criar_mensagem, interpretar_mensagem
import json

HOST = 'localhost'
PORTA_CLIENTES = 5000
PORTA_SECUNDARIOS = 5001
SERVIDOR_NOMES_HOST = 'localhost'
SERVIDOR_NOMES_PORTA = 5050

lista = ListaTarefas()
conexoes_secundarios = []

def registrar_no_servidor_de_nomes():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVIDOR_NOMES_HOST, SERVIDOR_NOMES_PORTA))
        msg = {
            "tipo": "registro",
            "nome": "servidor_lider",
            "ip": HOST,
            "porta": PORTA_CLIENTES
        }
        s.sendall(json.dumps(msg).encode())
        resposta = s.recv(1024).decode()
        print(f"[LÍDER] Registro no servidor de nomes: {resposta}")

def notificar_secundarios(mensagem_json):
    for conn in conexoes_secundarios:
        try:
            conn.sendall(mensagem_json.encode())
        except:
            conexoes_secundarios.remove(conn)

def tratar_cliente(conn, addr):
    print(f"[CLIENTE] Conectado: {addr}")
    while True:
        try:
            dados = conn.recv(1024).decode()
            if not dados:
                break

            mensagem = interpretar_mensagem(dados)
            tipo = mensagem.get("tipo")
            comando = mensagem.get("comando")
            dados_msg = mensagem.get("dados", {})

            if tipo != "comando":
                resposta = criar_mensagem("erro", "lider", None, {"mensagem": "Tipo inválido para cliente."})
                conn.sendall(resposta.encode())
                continue

            if comando == "add":
                resposta_texto = lista.adicionar(dados_msg.get("tarefa", ""))
            elif comando == "remove":
                resposta_texto = lista.remover(dados_msg.get("tarefa", ""))
            elif comando == "edit":
                resposta_texto = lista.editar(dados_msg.get("antiga", ""), dados_msg.get("nova", ""))
            elif comando == "list":
                resposta_texto = lista.listar()
            else:
                resposta_texto = "Comando inválido."

            resposta = criar_mensagem("resposta", "lider", comando, {"mensagem": resposta_texto})
            conn.sendall(resposta.encode())

            if comando in ["add", "remove", "edit"]:
                evento = criar_mensagem("evento", "lider", comando, dados_msg)
                notificar_secundarios(evento)

        except Exception as e:
            print(f"[ERRO] Cliente {addr}: {e}")
            break
    conn.close()

def aceitar_clientes():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORTA_CLIENTES))
        s.listen()
        print(f"[LÍDER] Aguardando clientes em {HOST}:{PORTA_CLIENTES}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=tratar_cliente, args=(conn, addr), daemon=True).start()

def aceitar_secundarios():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORTA_SECUNDARIOS))
        s.listen()
        print(f"[LÍDER] Aguardando réplicas em {HOST}:{PORTA_SECUNDARIOS}")
        while True:
            conn, _ = s.accept()
            conexoes_secundarios.append(conn)
            print("[LÍDER] Réplica conectada.")

if __name__ == "__main__":
    registrar_no_servidor_de_nomes()
    threading.Thread(target=aceitar_clientes, daemon=True).start()
    aceitar_secundarios()
