from datetime import datetime

import httpx
from agentecore import OpenAI, Agent
from config import ROUTER, MODEL, AI_API_KEY, PROMPT
from lib.mcp_servers import MCPServers
from tools import TOOLS

ERRORI_CHIAVE = {401, 402, 403, 429}


class OpenAIMultiKey(OpenAI):
    def __init__(self, api_keys: list[str], **kwargs):
        super().__init__(api_key=api_keys[0], **kwargs)
        self.api_keys = api_keys
        self.indice = 0

    def _post(self, url, headers, payload):
        while True:
            headers = {**headers, "Authorization": f"Bearer {self.api_key}"}
            try:
                return super()._post(url, headers, payload)
            except httpx.HTTPStatusError as e:
                ultima = self.indice == len(self.api_keys) - 1
                if e.response.status_code not in ERRORI_CHIAVE or ultima:
                    raise
                self.indice += 1
                self.api_key = self.api_keys[self.indice]
                #print(f"Chiave {self.indice} fallita ({e.response.status_code}), provo la {self.indice + 1}")



client = OpenAIMultiKey(
    api_keys=[v for k, v in AI_API_KEY.items() if k.startswith("openrouter")],
    model_name=MODEL,
    base_url=ROUTER,
)

mcp_servers = MCPServers()
agent = Agent(
    client=client,
    tools=TOOLS + mcp_servers.tools,
    system_prompt=f"{PROMPT}\n\nData di oggi: {datetime.now():%Y-%m-%d}.",
)


def run_agent(text):
    return agent.run(input=text).text
