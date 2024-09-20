import subprocess
import shutil
from rich.console import Console

console = Console()

def run_tests(project_dir):
    console.print("[bold cyan]Running tests...[/bold cyan]")
    npm_path = shutil.which('npm')
    if npm_path is None:
        console.print("[red]Error: 'npm' command not found. Please install Node.js.[/red]")
        return False, ""
    try:
        result = subprocess.run([npm_path, 'test'], cwd=project_dir, capture_output=True, text=True, check=True)
        console.print("[green]Tests passed successfully.[/green]")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        console.print("[red]Tests failed.[/red]")
        return False, e.stdout + e.stderr
    except Exception as e:
        console.print(f"[red]An error occurred while running tests: {e}[/red]")
        return False, ""

def run_linter(project_dir):
    console.print("[bold cyan]Running linter...[/bold cyan]")
    npx_path = shutil.which('npx')
    if npx_path is None:
        console.print("[red]Error: 'npx' command not found. Please install Node.js.[/red]")
        return -1, ""
    try:
        result = subprocess.run([npx_path, 'eslint', '.'], cwd=project_dir, capture_output=True, text=True)
        lint_errors = parse_lint_errors(result.stdout)
        if lint_errors == 0:
            console.print("[green]No linting errors found.[/green]")
        else:
            console.print(f"[yellow]{lint_errors} linting errors found.[/yellow]")
        return lint_errors, result.stdout
    except Exception as e:
        console.print(f"[red]An error occurred while running linter: {e}[/red]")
        return -1, ""

import re

def parse_lint_errors(lint_output):
    """
    Parses ESLint output to count the number of errors.

    Args:
        lint_output (str): The output from the ESLint command.

    Returns:
        int: The total number of lint errors found.
    """
    error_count = 0
    # Regex pattern to match ESLint error lines
    error_line_pattern = re.compile(r'^\s*\d+:\d+\s+error\s+')

    for line in lint_output.splitlines():
        if error_line_pattern.match(line):
            error_count += 1

    return error_count


def calculate_reward(tests_passed, lint_errors, comparison_result):
    reward = 0
    reward += 5 if comparison_result else -5
    reward += 10 if tests_passed else -10
    reward -= max(lint_errors, 0)
    return reward
