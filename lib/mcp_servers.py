import asyncio
import atexit
import json
import os
import re
import threading
from contextlib import AsyncExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx2
from agentecore import Tool
from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "mcp_servers.json"
LOG_FILE = BASE_DIR / "mcp.log"

CONNECT_TIMEOUT = 30
CALL_TIMEOUT = 120


@dataclass
class MCPTool(Tool):
    """Tool che arriva da un server MCP: lo schema è già JSON Schema e lo valida il server."""

    schema: dict[str, Any] | None = None

    @property
    def parameters(self) -> dict[str, Any]:
        return self.schema or {"type": "object", "properties": {}}

    def _validated_kwargs(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return arguments


def _expand(value: str) -> str:
    """Sostituisce ${VAR} con la variabile d'ambiente, così i segreti restano fuori dal file."""
    def sostituisci(m: re.Match) -> str:
        if m.group(1) not in os.environ:
            raise KeyError(f"variabile d'ambiente {m.group(1)} non impostata")
        return os.environ[m.group(1)]
    return re.sub(r"\$\{(\w+)\}", sostituisci, value)


def _tool_name(server: str, tool: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", f"{server}__{tool}")[:64]


def _result_text(result) -> str:
    parti = []
    for c in result.content:
        if c.type == "text":
            parti.append(c.text)
        elif c.type == "resource" and hasattr(c.resource, "text"):
            parti.append(c.resource.text)
        elif c.type == "resource_link":
            parti.append(f"[risorsa: {c.uri}]")
        else:
            parti.append(f"[contenuto {c.type} non supportato]")
    if not parti and result.structured_content is not None:
        parti.append(json.dumps(result.structured_content, ensure_ascii=False))
    return "\n".join(parti)


class MCPServers:
    def __init__(self, config_file: Path = CONFIG_FILE):
        self.tools: list[Tool] = []
        self.errors: dict[str, str] = {}
        self._config = self._load(config_file)
        self._loop = asyncio.new_event_loop()
        self._stop: asyncio.Event | None = None
        self._tasks: list[asyncio.Future] = []
        self._log = None
        if not self._config:
            return

        threading.Thread(target=self._loop.run_forever, name="mcp", daemon=True).start()
        self._log = open(LOG_FILE, "a", encoding="utf-8")
        self._stop = self._call(self._new_event())
        atexit.register(self.close)

        for name, cfg in self._config.items():
            ready = self._loop.create_future()
            self._tasks.append(asyncio.run_coroutine_threadsafe(self._serve(name, cfg, ready), self._loop))
            try:
                client, tools = self._call(self._wait(ready), CONNECT_TIMEOUT)
            except Exception as e:
                self._tasks[-1].cancel()
                while isinstance(e, BaseExceptionGroup) and len(e.exceptions) == 1:
                    e = e.exceptions[0]
                self.errors[name] = f"{type(e).__name__}: {e}"
                continue
            self.tools += [self._wrap(name, client, t) for t in tools]

    @staticmethod
    def _load(config_file: Path) -> dict[str, dict]:
        if not config_file.exists():
            return {}
        data = json.loads(config_file.read_text(encoding="utf-8"))
        return {k: v for k, v in data.get("mcpServers", {}).items() if not v.get("disabled")}

    @staticmethod
    async def _new_event() -> asyncio.Event:
        return asyncio.Event()

    @staticmethod
    async def _wait(future: asyncio.Future):
        return await future

    def _call(self, coro, timeout: float | None = None):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)

    def _transport(self, cfg: dict, stack: AsyncExitStack):
        if "url" in cfg:
            headers = {k: _expand(v) for k, v in cfg.get("headers", {}).items()}
            http = httpx2.AsyncClient(headers=headers, timeout=httpx2.Timeout(30, read=300))
            stack.push_async_callback(http.aclose)
            return streamable_http_client(_expand(cfg["url"]), http_client=http)
        params = StdioServerParameters(
            command=cfg["command"],
            args=[_expand(a) for a in cfg.get("args", [])],
            env={k: _expand(v) for k, v in cfg.get("env", {}).items()},
            cwd=cfg.get("cwd"),
        )
        return stdio_client(params, errlog=self._log)

    async def _serve(self, name: str, cfg: dict, ready: asyncio.Future) -> None:
        try:
            async with AsyncExitStack() as stack:
                client = await stack.enter_async_context(Client(self._transport(cfg, stack)))
                tools, cursor = [], None
                while True:
                    page = await client.list_tools(cursor=cursor)
                    tools += page.tools
                    cursor = page.next_cursor
                    if cursor is None:
                        break
                allowed = cfg.get("tools")
                if allowed is not None:
                    tools = [t for t in tools if t.name in allowed]
                ready.set_result((client, tools))
                await self._stop.wait()
        except Exception as e:
            if not ready.done():
                ready.set_exception(e)

    def _wrap(self, server: str, client: Client, t) -> MCPTool:
        def chiama(**arguments):
            result = self._call(client.call_tool(t.name, arguments), CALL_TIMEOUT)
            text = _result_text(result)
            if result.is_error:
                raise RuntimeError(text or "il server ha restituito un errore")
            return text

        return MCPTool(
            name=_tool_name(server, t.name),
            description=f"[{server}] {t.description or t.title or t.name}",
            fn=chiama,
            args_model=BaseModel,
            schema=t.input_schema,
        )

    def close(self) -> None:
        if self._stop is None:
            return
        self._loop.call_soon_threadsafe(self._stop.set)
        for task in self._tasks:
            try:
                task.result(10)
            except Exception:
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._stop = None
        if self._log:
            self._log.close()
