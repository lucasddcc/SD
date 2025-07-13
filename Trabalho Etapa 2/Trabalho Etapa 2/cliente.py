# cliente.py
import socket

HOST = 'localhost'
PORTA = 5000

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORTA))
        print("[CLIENTE] Conectado ao servidor líder.")
        print("Comandos: add;TAREFA | remove;TAREFA | edit;VELHA;NOVA | list")

        while True:
            comando = input(">>> ")
            if comando.lower() in ["exit", "quit"]:
                break
            s.sendall(comando.encode())
            resposta = s.recv(1024).decode()
            print("[RESPOSTA]", resposta)

if __name__ == "__main__":
    main()
