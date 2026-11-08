from datetime import datetime

from agentecore import tool


@tool
def ora_attuale() -> str:
    """Restituisce data e ora attuali."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
