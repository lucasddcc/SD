# servidor_lider.py
import socket
import threading
from tarefas import ListaTarefas

HOST = 'localhost'
PORTA_CLIENTES = 5000
PORTA_SECUNDARIOS = 5001

lista = ListaTarefas()
conexoes_secundarios = []

def notificar_secundarios(mensagem):
    for conn in conexoes_secundarios:
        try:
            conn.sendall(mensagem.encode())
        except:
            conexoes_secundarios.remove(conn)

def tratar_cliente(conn, addr):
    print(f"[CLIENTE] Conectado: {addr}")
    while True:
        try:
            dados = conn.recv(1024).decode()
            if not dados:
                break
            print(f"[CLIENTE] {addr}: {dados}")

            cmd, *args = dados.split(';')
            if cmd == "add":
                resposta = lista.adicionar(args[0])
            elif cmd == "remove":
                resposta = lista.remover(args[0])
            elif cmd == "edit":
                resposta = lista.editar(args[0], args[1])
            elif cmd == "list":
                resposta = lista.listar()
            else:
                resposta = "Comando inválido."

            conn.sendall(resposta.encode())

            # Notificar secundários sobre atualizações (exceto "list")
            if cmd in ["add", "remove", "edit"]:
                notificar_secundarios(dados)

        except:
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
    threading.Thread(target=aceitar_clientes, daemon=True).start()
    aceitar_secundarios()
