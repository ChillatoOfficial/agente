import importlib
import pkgutil

from agentecore import Tool

# Raccoglie in automatico ogni funzione decorata con @tool nei file di questa cartella
TOOLS: list[Tool] = []

for modulo in pkgutil.iter_modules(__path__):
    if modulo.name.startswith("_"):
        continue
    mod = importlib.import_module(f"{__name__}.{modulo.name}")
    TOOLS.extend(v for v in vars(mod).values() if isinstance(v, Tool))
