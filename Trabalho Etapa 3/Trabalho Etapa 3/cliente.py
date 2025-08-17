# cliente.py
import socket
import json
from mensagens import criar_mensagem, interpretar_mensagem

SERVIDOR_NOMES_HOST = 'localhost'
SERVIDOR_NOMES_PORTA = 5050

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
            print("[CLIENTE] Erro ao localizar líder:", resposta.get("mensagem"))
            return None, None

def main():
    ip_lider, porta_lider = descobrir_lider()
    if not ip_lider:
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip_lider, porta_lider))
        print("[CLIENTE] Conectado ao servidor líder.")
        print("Comandos disponíveis:")
        print("add;TAREFA | remove;TAREFA | edit;VELHA;NOVA | list")
        print("exit ou quit para sair")

        while True:
            comando_raw = input(">>> ")
            if comando_raw.lower() in ["exit", "quit"]:
                break

            partes = comando_raw.split(";")
            comando = partes[0]

            if comando == "add" and len(partes) == 2:
                msg = criar_mensagem("comando", "cliente", "add", {"tarefa": partes[1]})
            elif comando == "remove" and len(partes) == 2:
                msg = criar_mensagem("comando", "cliente", "remove", {"tarefa": partes[1]})
            elif comando == "edit" and len(partes) == 3:
                msg = criar_mensagem("comando", "cliente", "edit", {"antiga": partes[1], "nova": partes[2]})
            elif comando == "list":
                msg = criar_mensagem("comando", "cliente", "list", {})
            else:
                print("[CLIENTE] Comando inválido.")
                continue

            s.sendall(msg.encode())
            resposta = s.recv(1024).decode()
            resposta_dic = interpretar_mensagem(resposta)
            print("[RESPOSTA]", resposta_dic.get("dados", {}).get("mensagem", "Erro."))

if __name__ == "__main__":
    main()
