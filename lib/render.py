from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()


def render_response(response: str):
    if not response:
        return

    markdown = Markdown(
        response,
        code_theme="monokai",
        justify="left"
    )

    console.print()
    console.print(
        markdown,
        soft_wrap=True
    )
    console.print()