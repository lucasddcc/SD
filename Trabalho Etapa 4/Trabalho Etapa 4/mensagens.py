# mensagens.py
import json
from typing import Optional, Dict, Any

def criar_mensagem(
    tipo: str,
    origem: str,
    comando: Optional[str] = None,
    dados: Optional[Dict[str, Any]] = None,
    *,
    id: Optional[str] = None,
    lamport: Optional[int] = None,
    vector: Optional[Dict[str, int]] = None
) -> str:
    """
    Monta uma mensagem JSON com campos padronizados.
    Campos opcionais só são incluídos se não forem None.
    """
    msg = {
        "tipo": tipo,
        "origem": origem,
        "dados": dados or {}
    }
    if comando is not None:
        msg["comando"] = comando
    if id is not None:
        msg["id"] = id
    if lamport is not None:
        msg["lamport"] = lamport
    if vector is not None:
        msg["vector"] = vector
    return json.dumps(msg, ensure_ascii=False)

def interpretar_mensagem(mensagem_json: str) -> dict:
    """
    Parsing de mensagem JSON. Em caso de erro, retorna estrutura 'erro'.
    """
    try:
        return json.loads(mensagem_json)
    except json.JSONDecodeError:
        return {
            "tipo": "erro",
            "origem": "sistema",
            "dados": {"mensagem": "Mensagem inválida"}
        }
