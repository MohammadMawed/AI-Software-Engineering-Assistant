import os
from git import Repo, GitCommandError, InvalidGitRepositoryError
from rich.console import Console

console = Console()

def clone_or_pull_repo(repo_url, local_dir, pull_latest=False):
    try:
        if os.path.exists(local_dir):
            repo = Repo(local_dir)
            if pull_latest:
                console.print("[bold cyan]Pulling latest changes...[/bold cyan]")
                repo.remotes.origin.pull()
                console.print("[green]Repository updated successfully.[/green]")
            else:
                console.print("[yellow]Using existing repository without pulling updates.[/yellow]")
        else:
            console.print("[bold cyan]Cloning repository...[/bold cyan]")
            Repo.clone_from(repo_url, local_dir)
            console.print("[green]Repository cloned successfully.[/green]")
        return True
    except InvalidGitRepositoryError:
        console.print("[red]The specified directory is not a valid Git repository.[/red]")
        return False
    except GitCommandError as e:
        console.print(f"[red]Git command error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")
        return False
