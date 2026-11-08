from agentecore import tool
import subprocess
import sys
import tempfile
import os
from pathlib import Path

@tool
def python_execute(code: str):
    """Esegue codice Python in un processo separato e restituisce stdout e stderr.

    Usalo per calcoli, prove di codice o elaborazione di dati.
    L'esecuzione si interrompe dopo 10 secondi.

    Args:
        code: il codice Python da eseguire. Usa print() per vedere i risultati.
    """
    if not isinstance(code, str) or not code.strip():
        return {"success": False, "error": "Codice vuoto"}

    # Limite dimensione codice
    if len(code) > 10000:
        return {"success": False, "error": "Codice troppo lungo"}

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            encoding="utf-8",
            delete=False
        ) as file:
            file.write(code)
            temp_path = file.name

        result = subprocess.run(
            [sys.executable, "-I", temp_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=tempfile.gettempdir()
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:10000],
            "return_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Esecuzione interrotta: timeout di 10 secondi"
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)