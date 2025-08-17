# servidor_secundario.py
import socket
import json
from tarefas import ListaTarefas
from mensagens import interpretar_mensagem

SERVIDOR_NOMES_HOST = 'localhost'
SERVIDOR_NOMES_PORTA = 5050

lista = ListaTarefas()

def descobrir_lider():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVIDOR_NOMES_HOST, SERVIDOR_NOMES_PORTA))
        consulta = {
            "tipo": "consulta",
            "nome": "servidor_lider"
        }
        s.sendall(json.dumps(consulta).encode())
        resposta = json.loads(s.recv(1024).decode())
        if resposta.get("status") == "ok":
            return resposta["ip"], resposta["porta"]
        else:
            print("[RÉPLICA] Erro ao localizar líder:", resposta.get("mensagem"))
            return None, None

def processar_evento(mensagem):
    comando = mensagem.get("comando")
    dados = mensagem.get("dados", {})

    if comando == "add":
        print(lista.adicionar(dados.get("tarefa", "")))
    elif comando == "remove":
        print(lista.remover(dados.get("tarefa", "")))
    elif comando == "edit":
        print(lista.editar(dados.get("antiga", ""), dados.get("nova", "")))
    else:
        print("[RÉPLICA] Evento desconhecido:", mensagem)

def main():
    ip_lider, porta_lider = descobrir_lider()
    if not ip_lider:
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip_lider, 5001))
        print("[RÉPLICA] Conectado ao líder.")

        while True:
            try:
                dados = s.recv(1024).decode()
                if not dados:
                    break
                mensagem = interpretar_mensagem(dados)
                if mensagem.get("tipo") == "evento":
                    print(f"[RÉPLICA] Evento recebido: {mensagem}")
                    processar_evento(mensagem)
            except Exception as e:
                print(f"[RÉPLICA] Erro na comunicação: {e}")
                break

if __name__ == "__main__":
    main()
