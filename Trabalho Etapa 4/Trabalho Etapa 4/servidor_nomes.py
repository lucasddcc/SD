# servidor_nomes.py
import socket
import threading
import json

SERVIDOR_HOST = 'localhost'
SERVIDOR_PORTA = 5050
registro_servicos = {}  # nome: (ip, porta)

def tratar_cliente(conn, addr):
    print(f"[NOMES] Conexão de {addr}")
    while True:
        try:
            dados = conn.recv(1024).decode()
            if not dados:
                break

            mensagem = json.loads(dados)
            tipo = mensagem.get("tipo")

            if tipo == "registro":
                nome = mensagem.get("nome")
                ip = mensagem.get("ip")
                porta = mensagem.get("porta")
                registro_servicos[nome] = (ip, porta)
                print(f"[NOMES] Serviço registrado: {nome} → {ip}:{porta}")
                resposta = {"status": "ok", "mensagem": f"{nome} registrado com sucesso."}
                conn.sendall(json.dumps(resposta).encode())

            elif tipo == "consulta":
                nome = mensagem.get("nome")
                if nome in registro_servicos:
                    ip, porta = registro_servicos[nome]
                    resposta = {"status": "ok", "ip": ip, "porta": porta}
                else:
                    resposta = {"status": "erro", "mensagem": f"Serviço '{nome}' não encontrado."}
                conn.sendall(json.dumps(resposta).encode())

            else:
                conn.sendall(json.dumps({"status": "erro", "mensagem": "Tipo de mensagem desconhecido."}).encode())
        except:
            break

    conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((SERVIDOR_HOST, SERVIDOR_PORTA))
        s.listen()
        print(f"[NOMES] Servidor de nomes ativo em {SERVIDOR_HOST}:{SERVIDOR_PORTA}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=tratar_cliente, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
