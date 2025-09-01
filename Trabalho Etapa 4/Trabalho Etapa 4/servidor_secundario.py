# servidor_secundario.py
import socket
import json
from tarefas import ListaTarefas
from mensagens import interpretar_mensagem
from relogios import LamportClock, VectorClock

SERVIDOR_NOMES_HOST = 'localhost'
SERVIDOR_NOMES_PORTA = 5050

REPLICA_ID = "secundario"
lamport = LamportClock()
vclock = VectorClock(my_id=REPLICA_ID)

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
    # Atualiza relógios no recebimento
    lamport.receive(mensagem.get("lamport"))
    vclock.merge(mensagem.get("vector"))

    origem = mensagem.get("origem", "desconhecida")
    comando = mensagem.get("comando")
    dados = mensagem.get("dados", {})

    # Aplica o efeito do evento na lista local
    resultado = ""
    if comando == "add":
        resultado = lista.adicionar(dados.get("tarefa", ""))
    elif comando == "remove":
        resultado = lista.remover(dados.get("tarefa", ""))
    elif comando == "edit":
        resultado = lista.editar(dados.get("antiga", ""), dados.get("nova", ""))
    else:
        resultado = f"Evento desconhecido: {mensagem}"

    # Impressão “limpa”: cabeçalho do evento, resultado e metadados em linhas separadas
    print("[EVENTO]")
    print(f"origem={origem} | comando={comando} | dados={dados}")
    print("[APLICAÇÃO]", resultado)
    print(f"[META] L={lamport.now()}, V={vclock.snapshot()}")

def main():
    ip_lider, porta_lider = descobrir_lider()
    if not ip_lider:
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Observação: porta de eventos permanece 5001 (conforme a Etapa 3 atual)
        s.connect((ip_lider, 5001))
        print("[RÉPLICA] Conectado ao líder.")

        while True:
            try:
                dados = s.recv(1024).decode()
                if not dados:
                    break
                mensagem = interpretar_mensagem(dados)
                if mensagem.get("tipo") == "evento":
                    processar_evento(mensagem)
            except Exception as e:
                print(f"[RÉPLICA] Erro na comunicação: {e}")
                break

if __name__ == "__main__":
    main()
