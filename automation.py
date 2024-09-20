import subprocess
import sys
import shutil
from rich.console import Console

console = Console()

def automate_vscode_and_cmd():
    console.print("[bold cyan]Automating VSCode and Command Prompt/Terminal...[/bold cyan]")
    try:
        # Check if 'code' command is available
        if shutil.which('code') is None:
            raise FileNotFoundError("VSCode command 'code' not found. Ensure VSCode is installed and added to your PATH.")

        # Open VSCode
        subprocess.Popen(['code'])

        # Open Command Prompt or Terminal based on the operating system
        if sys.platform.startswith('win'):
            subprocess.Popen(['cmd', '/K'])
        elif sys.platform.startswith('darwin'):  # macOS
            subprocess.Popen(['open', '-a', 'Terminal'])
        elif sys.platform.startswith('linux'):
            # Try to open the default terminal
            terminals = ['gnome-terminal', 'konsole', 'x-terminal-emulator', 'xterm']
            for term in terminals:
                if shutil.which(term):
                    subprocess.Popen([term])
                    break
            else:
                console.print("[yellow]No known terminal emulator found.[/yellow]")
        else:
            console.print("[yellow]Unsupported operating system.[/yellow]")

        console.print("[green]VSCode and Command Prompt/Terminal opened successfully.[/green]")
    except Exception as e:
        console.print(f"[yellow]Could not automate VSCode and Command Prompt/Terminal: {e}[/yellow]")
        console.print("[yellow]You may need to open these manually.[/yellow]")
