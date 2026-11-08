<div align="center">

<img src="https://i.pinimg.com/736x/0b/5a/d1/0b5ad148cc6e9d2bc32cb891fbf45924.jpg" alt="AGENTE" width="30%"/>

# AGENTE

**A personal AI agent for your terminal, with custom tools and MCP servers.**

by Chillato

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Licenza: MIT](https://img.shields.io/badge/licenza-MIT-green)](LICENSE)
![Stato: release](https://img.shields.io/badge/stato-release-blue)

[Features](#-features) •
[Installation](#-installation) •
[Configuration](#%EF%B8%8F-configuration) •
[MCP servers](#-mcp-servers) •
[Custom tools](#-custom-tools) •
[Roadmap](#-roadmap)

</div>

---

## ✨ Features

- 💬 **Terminal chat** with a rich interface built on `rich` and `prompt_toolkit`
- 🧠 **Any model on [OpenRouter](https://openrouter.ai)**, powered by the custom library [agentecore](https://github.com/ChillatoOfficial/agentecore)
- 🔌 **MCP servers**, both local (`command`) and remote (`url`)
- 🛠️ **Built-in tools**, plus your own with a single decorator

### Built-in tools

| Tool | What it does | Needs |
|---|---|---|
| `ricerca_web` | Searches the web for up-to-date information | Tavily key |
| `tiktok` | Finds TikTok videos with link, author and text | Tavily key |
| `tmdb` | Searches movies and returns plot, rating, cast and director | TMDB key |
| `python_execute` | Runs Python code in a separate process | — |
| `ora_attuale` | Returns the current date and time | — |

## 📦 Installation

Requires **Python 3.10+**.

```bash
git clone https://github.com/ChillatoOfficial/agente.git
cd agente

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python3 main.py
```

`requirements.txt` also installs the MCP dependencies from `requirements-mcp.txt`.

## ⚙️ Configuration

Copy `config.example.py` to `config.py` and fill in your keys:

```bash
cp config.example.py config.py      # Windows: copy config.example.py config.py
```

| Setting | Description |
|---|---|
| `AI_API_KEY` | API keys: `openrouter` (required), `tavily`, `tmdb` |
| `ROUTER` | OpenAI-compatible endpoint (default: OpenRouter) |
| `MODEL` | Model to use, e.g. `nvidia/nemotron-3.5-lightning:free` |
| `PROMPT` | The agent's system prompt |

> [!WARNING]
> Never commit `config.py` with your real keys in it.

## 🔌 MCP servers

Copy `mcp_servers.example.json` to `mcp_servers.json` and add your servers:

```json
{
  "mcpServers": {
    "esempio_locale": {
      "command": "npx",
      "args": ["-y", "nome-del-pacchetto-mcp"],
      "env": {"API_KEY": "${ESEMPIO_API_KEY}"},
      "tools": ["solo_questo_tool", "e_questo"]
    },
    "esempio_remoto": {
      "url": "https://esempio.com/mcp",
      "headers": {"Authorization": "Bearer ${ESEMPIO_TOKEN}"},
      "disabled": true
    }
  }
}
```

| Field | Description |
|---|---|
| `command` / `args` | Starts a local server over stdio |
| `url` / `headers` | Connects to a remote server over HTTP |
| `env` | Environment variables passed to the server |
| `tools` | Exposes only these tools (optional; default: all) |
| `disabled` | Set to `true` to skip the server |

`${VAR}` is replaced with the matching environment variable, so secrets stay out of the file.

## 🛠️ Custom tools

Create a file in `tools/` and decorate a function with `@tool`. It is loaded automatically at startup.

```python
from agentecore import tool


@tool
def somma(a: int, b: int) -> int:
    """utilizza questo tool per sommare due numeri."""
    return a + b
```

The docstring tells the model when to use the tool, so make it clear.

## 🗺️ Roadmap

- [ ] Gateway
- [ ] Discord bot to connect the agent
- [ ] WhatsApp bot to connect the agent
