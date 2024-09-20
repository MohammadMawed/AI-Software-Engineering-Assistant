import os
import shutil
import subprocess
from rich.console import Console
import openai
from rich.panel import Panel

console = Console()

def parse_files_and_open_in_vscode(project_dir):
    console.print("[bold cyan]Parsing files and opening in VSCode...[/bold cyan]")
    try:
        # Determine target file name (modify as needed based on plan)
        target_file = os.path.join(project_dir, 'components', 'TargetComponent.js')
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write("// TargetComponent.js\n")

        # Check if 'code' command is available
        if shutil.which('code') is None:
            raise FileNotFoundError("VSCode command 'code' not found. Ensure VSCode is installed and added to your PATH.")

        subprocess.run(['code', target_file], check=True)
        console.print(f"[green]Opened {target_file} in VSCode.[/green]")
        return target_file
    except Exception as e:
        console.print(f"[red]Error parsing files or opening in VSCode: {e}[/red]")
        return None


def generate_code_from_plan(plan):
    """
    Generates code based on the provided implementation plan using OpenAI's API.

    Args:
        plan (str): The implementation plan outlining the steps.

    Returns:
        str: The generated code.
    """
    console.print("[bold cyan]Generating code from plan using OpenAI...[/bold cyan]")

    # Load the OpenAI API key from environment variables
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        console.print("[red]Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.[/red]")
        return None

    prompt = f"""
    Based on the following implementation plan, generate the complete code necessary for a Next.js project using React and Tailwind CSS.
    Ensure the code is complete, follows best practices, and is ready for production use.
    Do not include any markdown formatting or placeholders.

    Implementation Plan:
    {plan}

    Generated Code:
    """

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1500,
            temperature=0,
            n=1,
            stop=None,
        )
        generated_code = response.choices[0].text.strip()
        console.print(Panel(generated_code, title="Generated Code", style="green"))
        return generated_code
    except Exception as e:
        console.print(f"[red]Error generating code: {e}[/red]")
        return None


def modify_code(code):
    """
    Modifies the generated code to improve its quality, fix issues, or refactor.

    Args:
        code (str): The original generated code.

    Returns:
        str: The modified code.
    """
    console.print("[bold cyan]Modifying the generated code using OpenAI...[/bold cyan]")

    prompt = f"""
    Review the following code and make any necessary improvements.
    Ensure the code follows best practices for Next.js, React, and Tailwind CSS.
    Fix any potential issues, improve readability, and optimize the code where possible.
    Do not include any markdown formatting or placeholders.

    Original Code:
    {code}

    Modified Code:
    """

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1500,
            temperature=0,
            n=1,
            stop=None,
        )
        modified_code = response.choices[0].text.strip()
        console.print(Panel(modified_code, title="Modified Code", style="green"))
        return modified_code
    except Exception as e:
        console.print(f"[red]Error modifying code: {e}[/red]")
        return None


def save_code_to_files(code, target_file):
    console.print("[bold cyan]Saving code to file...[/bold cyan]")
    with open(target_file, 'w', encoding='utf-8') as file:
        file.write(code)
    console.print(f"[green]Code saved to {target_file}[/green]")
