from lib.logo import console, create_session, current_mode, dashboard, right_column, separator
from lib.render import render_response
from agent import mcp_servers, run_agent
def main():
    dashboard()
    for name, error in mcp_servers.errors.items():
        console.print(f"Server MCP '{name}' non collegato: {error}", style="yellow", markup=False, highlight=False)
    session = create_session()

    while True:
        separator()
        try:
            text = session.prompt().strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not text:
            continue
        if text == "/exit":
            break
        if text == "/clear":
            console.clear()
            dashboard()
            continue
        if text == "/help":
            console.print(right_column())
            continue
        with console.status("in corso...", spinner="dots", spinner_style="bold cyan"):
            response = run_agent(text)
        render_response(f"{response}")


if __name__ == "__main__":
    main()