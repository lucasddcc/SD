# servidor_secundario.py
import socket
from tarefas import ListaTarefas

HOST = 'localhost'
PORTA = 5001

lista = ListaTarefas()

def processar_mensagem(mensagem):
    cmd, *args = mensagem.split(';')
    if cmd == "add":
        print(lista.adicionar(args[0]))
    elif cmd == "remove":
        print(lista.remover(args[0]))
    elif cmd == "edit":
        print(lista.editar(args[0], args[1]))

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORTA))
        print("[RÉPLICA] Conectado ao líder.")
        while True:
            dados = s.recv(1024).decode()
            if dados:
                print(f"[RÉPLICA] Comando recebido: {dados}")
                processar_mensagem(dados)

if __name__ == "__main__":
    main()
