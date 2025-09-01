# servidor_lider.py
import socket
import threading
import json
import itertools
import heapq
from tarefas import ListaTarefas
from mensagens import criar_mensagem, interpretar_mensagem
from relogios import LamportClock, VectorClock

HOST = 'localhost'
PORTA_CLIENTES = 5000
PORTA_SECUNDARIOS = 5001
SERVIDOR_NOMES_HOST = 'localhost'
SERVIDOR_NOMES_PORTA = 5050

lista = ListaTarefas()
conexoes_secundarios = []

# Etapa 4: relógios do líder
LEADER_ID = "lider"
lamport = LamportClock()
vclock = VectorClock(my_id=LEADER_ID)

# Exclusão mútua (centralizada no líder): fila ordenada por (lamport, client_id, seq)
fila_lock = threading.Lock()
fila_cond = threading.Condition(lock=fila_lock)
fila_heap = []
seq_counter = itertools.count()

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
    for conn in list(conexoes_secundarios):
        try:
            conn.sendall(mensagem_json.encode())
        except:
            try:
                conexoes_secundarios.remove(conn)
            except ValueError:
                pass

def worker_processar_fila():
    """
    Trabalhador que garante exclusão mútua:
    aplica comandos de escrita em ordem (lamport, client_id, seq),
    envia resposta ao cliente e publica evento às réplicas.
    """
    while True:
        with fila_cond:
            while not fila_heap:
                fila_cond.wait()
            lam_ts, cli_id, _, comando, dados, conn = heapq.heappop(fila_heap)

        # Evento local do líder ao processar:
        vclock.tick()
        lamport.tick()

        # Executa comando
        if comando == "add":
            resposta_texto = lista.adicionar(dados.get("tarefa", ""))
            evento_dados = {"tarefa": dados.get("tarefa", "")}
        elif comando == "remove":
            resposta_texto = lista.remover(dados.get("tarefa", ""))
            evento_dados = {"tarefa": dados.get("tarefa", "")}
        elif comando == "edit":
            resposta_texto = lista.editar(dados.get("antiga", ""), dados.get("nova", ""))
            evento_dados = {"antiga": dados.get("antiga", ""), "nova": dados.get("nova", "")}
        else:
            resposta_texto = "Comando inválido."
            evento_dados = {}

        # Resposta ao cliente com metadados de relógio
        resp = criar_mensagem(
            "resposta", "lider", comando, {"mensagem": resposta_texto},
            id=LEADER_ID, lamport=lamport.now(), vector=vclock.snapshot()
        )
        try:
            conn.sendall(resp.encode())
        except Exception as e:
            print(f"[LÍDER] Falha ao responder cliente {cli_id}: {e}")

        # Publica evento às réplicas com metadados
        if comando in ["add", "remove", "edit"]:
            evento = criar_mensagem(
                "evento", "lider", comando, evento_dados,
                id=LEADER_ID, lamport=lamport.now(), vector=vclock.snapshot()
            )
            notificar_secundarios(evento)

def tratar_cliente(conn, addr):
    print(f"[CLIENTE] Conectado: {addr}")
    try:
        while True:
            dados = conn.recv(1024).decode()
            if not dados:
                break

            mensagem = interpretar_mensagem(dados)
            tipo = mensagem.get("tipo")
            comando = mensagem.get("comando")
            dados_msg = mensagem.get("dados", {})
            cli_id = mensagem.get("id") or f"{addr[0]}:{addr[1]}"

            # Recepção: merge/receive relógios
            lamport.receive(mensagem.get("lamport"))
            vclock.merge(mensagem.get("vector"))

            if tipo != "comando":
                resp = criar_mensagem(
                    "erro", "lider", None, {"mensagem": "Tipo inválido para cliente."},
                    id=LEADER_ID, lamport=lamport.now(), vector=vclock.snapshot()
                )
                conn.sendall(resp.encode())
                continue

            if comando in ["add", "remove", "edit"]:
                # Enfileira com ordenação por (lamport do cliente, client_id) — justiça
                with fila_cond:
                    heapq.heappush(
                        fila_heap,
                        (mensagem.get("lamport", 0), str(cli_id), next(seq_counter), comando, dados_msg, conn)
                    )
                    fila_cond.notify()
                # Não respondemos aqui; a resposta sai pelo worker após aplicar.
            elif comando == "list":
                # Leitura não exige exclusão mútua global
                vclock.tick()
                lamport.tick()
                resposta_texto = lista.listar()
                resp = criar_mensagem(
                    "resposta", "lider", "list", {"mensagem": resposta_texto},
                    id=LEADER_ID, lamport=lamport.now(), vector=vclock.snapshot()
                )
                conn.sendall(resp.encode())
            else:
                vclock.tick()
                lamport.tick()
                resp = criar_mensagem(
                    "resposta", "lider", comando, {"mensagem": "Comando inválido."},
                    id=LEADER_ID, lamport=lamport.now(), vector=vclock.snapshot()
                )
                conn.sendall(resp.encode())

    except Exception as e:
        print(f"[ERRO] Cliente {addr}: {e}")
    finally:
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
    # Worker da fila (exclusão mútua)
    threading.Thread(target=worker_processar_fila, daemon=True).start()
    # Acceptors
    threading.Thread(target=aceitar_clientes, daemon=True).start()
    aceitar_secundarios()
