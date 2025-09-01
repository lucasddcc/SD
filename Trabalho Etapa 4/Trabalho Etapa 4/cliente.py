# cliente.py
import socket
import json
import uuid
from mensagens import criar_mensagem, interpretar_mensagem
from relogios import LamportClock, VectorClock

SERVIDOR_NOMES_HOST = 'localhost'
SERVIDOR_NOMES_PORTA = 5050

CLIENT_ID = f"cli-{uuid.uuid4().hex[:8]}"
lamport = LamportClock()
vclock = VectorClock(my_id=CLIENT_ID)

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
        print(f"[CLIENTE {CLIENT_ID}] Conectado ao servidor líder.")
        print("Comandos: add;TAREFA | remove;TAREFA | edit;VELHA;NOVA | list | exit")

        while True:
            comando_raw = input(">>> ")
            if comando_raw.lower() in ["exit", "quit"]:
                break

            partes = comando_raw.split(";")
            comando = partes[0]

            if comando == "add" and len(partes) == 2:
                dados = {"tarefa": partes[1]}
            elif comando == "remove" and len(partes) == 2:
                dados = {"tarefa": partes[1]}
            elif comando == "edit" and len(partes) == 3:
                dados = {"antiga": partes[1], "nova": partes[2]}
            elif comando == "list":
                dados = {}
            else:
                print("[CLIENTE] Comando inválido.")
                continue

            # Etapa 4: Lamport e Vetorial no envio
            lamport.tick()
            vclock.tick()
            msg = criar_mensagem(
                "comando", "cliente", comando, dados,
                id=CLIENT_ID, lamport=lamport.now(), vector=vclock.snapshot()
            )
            s.sendall(msg.encode())

            resposta = s.recv(1024).decode()
            resp = interpretar_mensagem(resposta)

            # Atualiza relógios com metadados do líder (se vierem)
            lamport.receive(resp.get("lamport"))
            v = resp.get("vector")
            if v is not None:
                vclock.merge(v)

            texto = resp.get("dados", {}).get("mensagem", "Erro.")
            print("[RESPOSTA]")
            print(texto)
            print(f"[META] L={lamport.now()}, V={vclock.snapshot()}")


if __name__ == "__main__":
    main()
