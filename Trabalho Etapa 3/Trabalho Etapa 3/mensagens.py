# mensagens.py
import json

def criar_mensagem(tipo: str, origem: str, comando: str = None, dados: dict = None) -> str:
    """
    Cria uma mensagem JSON estruturada para comunicação entre os componentes.

    :param tipo: 'comando', 'evento', 'registro', 'consulta'
    :param origem: 'cliente', 'lider', 'secundario', etc.
    :param comando: nome do comando, se aplicável (ex: 'add', 'remove', 'list')
    :param dados: dicionário com os dados específicos da mensagem
    :return: string JSON serializada
    """
    msg = {
        "tipo": tipo,
        "origem": origem,
        "comando": comando,
        "dados": dados or {}
    }
    return json.dumps(msg)


def interpretar_mensagem(mensagem_json: str) -> dict:
    """
    Faz o parsing de uma mensagem JSON recebida e retorna um dicionário.

    :param mensagem_json: string JSON recebida
    :return: dicionário com os campos da mensagem
    """
    try:
        return json.loads(mensagem_json)
    except json.JSONDecodeError:
        return {
            "tipo": "erro",
            "origem": "sistema",
            "comando": None,
            "dados": {"mensagem": "Mensagem inválida"}
        }
