import os
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML, FormattedText
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import MODEL, ROUTER

sys.stdout.reconfigure(encoding="utf-8")
console = Console()

color = {
    "celeste": "#27F5E0",
    "grigio": "#858585",
    "bianco": "#E5E5E5",
    "nero": "#252525",
}

COMMANDS = {
    "/help":  "Mostra i comandi disponibili",
    "/clear": "Pulisce lo schermo",
    "/exit":  "Esci da agente",
}

MODES = ["normal", "auto", "plan"]
state = {"mode": 0}

def provider_name() -> str:
    return ROUTER.replace("https://", "").split(".")[0]


def left_column() -> Panel:
    content = Group(
        Align.center(Text("⚡ Welcome back!", style=f"bold {color['celeste']}")),
        Text(""),
        Align.center(Text(f"{MODEL} | {provider_name()}", style=f"bold {color['grigio']}")),
    )
    return Panel(
        content,
        title="⬢ agente",
        title_align="center",
        border_style=f"bold {color['celeste']}",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def right_column() -> Panel:
    table = Table.grid(padding=(0, 2))
    for cmd, desc in COMMANDS.items():
        table.add_row(
            Text(cmd, style=f"bold {color['celeste']}"),
            Text(desc, style=color["grigio"]),
        )
    return Panel(
        table,
        title="comandi",
        title_align="center",
        border_style=color["grigio"],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def dashboard():
    layout = Table.grid(expand=True, padding=(0, 1))
    layout.add_column(ratio=1)
    layout.add_column(ratio=1)
    layout.add_row(left_column(), right_column())
    console.print(layout)


def separator():
    console.rule(style=color["grigio"])


def current_mode() -> str:
    return MODES[state["mode"]]


class SlashCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/") or " " in text:
            return
        for cmd, desc in COMMANDS.items():
            if cmd.startswith(text):
                yield Completion(cmd, start_position=-len(text),
                                 display=cmd, display_meta=desc)


kb = KeyBindings()

@kb.add("s-tab")
def _(event):
    state["mode"] = (state["mode"] + 1) % len(MODES)
    event.app.invalidate()


def toolbar():
    line = "─" * shutil.get_terminal_size().columns
    return HTML(
        f"<line>{line}</line>\n"
        f"<mode>⏵⏵ {current_mode()} mode</mode> "
        f"<hint>(shift+tab per cambiare)</hint>"
    )


style = Style.from_dict({
    "line": color["grigio"],
    "mode": f"{color['celeste']} bold",
    "hint": color["grigio"],
    "prompt": f"{color['celeste']} bold",
    "placeholder": f"{color['grigio']} italic",
    "completion-menu": "bg:default",
    "completion-menu.completion": f"bg:default {color['grigio']}",
    "completion-menu.completion.current": f"bg:default {color['celeste']} bold",
    "completion-menu.meta.completion": f"bg:default {color['grigio']}",
    "completion-menu.meta.completion.current": f"bg:default {color['bianco']}",
    "scrollbar.background": "bg:default",
    "scrollbar.button": "bg:default",
})

PROMPT = HTML("<prompt> ❯ </prompt>")


class Placeholder(Processor):
    """Mostra un testo grigio quando l'input è vuoto."""
    def apply_transformation(self, ti):
        if not ti.document.text and ti.lineno == 0:
            return Transformation(ti.fragments + [
                ("class:placeholder", "scrivi un messaggio o / per i comandi")
            ])
        return Transformation(ti.fragments)


@kb.add("c-c")
def _(event):
    event.app.exit(exception=KeyboardInterrupt)

@kb.add("c-d")
def _(event):
    event.app.exit(exception=EOFError)


def status():
    return HTML(f" <mode>⏵⏵ {current_mode()} mode</mode> "
                f"<hint>(shift+tab per cambiare)</hint>")


class InputBox:
    def __init__(self):
        self.buffer = Buffer(
            completer=SlashCompleter(),
            complete_while_typing=True,
            multiline=False,
            accept_handler=self._accept,
        )
        layout = HSplit([
            VSplit([
                Window(FormattedTextControl(PROMPT), dont_extend_width=True),
                Window(BufferControl(self.buffer, input_processors=[Placeholder()]),
                       dont_extend_height=True),
            ]),
            CompletionsMenu(max_height=6),
            Window(height=1, char="─", style="class:line"),
            Window(FormattedTextControl(status), height=1),
        ])
        self.app = Application(
            layout=Layout(layout, focused_element=self.buffer),
            key_bindings=kb,
            style=style,
            full_screen=False,
            erase_when_done=True,
        )

    def _accept(self, buff):
        self.app.exit(result=buff.text)
        return False             

    def prompt(self) -> str:
        text = self.app.run()
        print_formatted_text(HTML("<prompt> ❯ </prompt>") + HTML(f"{text}"), style=style) if False else \
            print_formatted_text(FormattedText([(f"{color['celeste']} bold", " ❯ "), ("", text)]))
        return text


def create_session() -> InputBox:
    return InputBox()

if __name__ == "__main__":
    dashboard()