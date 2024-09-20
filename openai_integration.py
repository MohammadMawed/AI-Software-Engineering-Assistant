import os
import subprocess
import shutil
from dotenv import load_dotenv
from openai import OpenAI
from rich.panel import Panel
from rich.console import Console
import subprocess

load_dotenv()  # Load environment variables from .env file
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
console = Console()

def plan_task(description, relevant_file_contents):
    console.print("[bold cyan]Generating implementation plan using OpenAI...[/bold cyan]")
    context = "\n\n".join([f"File: {path}\n{content}" for path, content in relevant_file_contents.items()])
    prompt = f"""
    You are a software engineer assistant. Break down the following task into smaller, actionable steps for implementation in a Next.js project using React and Tailwind CSS.
    Consider the context of the existing code provided below.
    Task:
    {description}
    Existing Code Context:
    {context}
    Provide the steps as a numbered list, including specific file names and locations where changes should be made.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0
        )
        plan = response.choices[0].message.content.strip()
        console.print(Panel(plan, title="Generated Plan", style="cyan"))
        return plan
    except Exception as e:
        console.print(f"[red]Error generating plan: {e}[/red]")
        return None


def generate_code(prompt, file_contents):
    """
    Generates code based on the prompt and file contents using OpenAI's API.

    Args:
        prompt (str): The instruction or task description for code generation.
        file_contents (str): The current file content to be used in the generation process.

    Returns:
        str: The generated code.
    """
    console.print("[bold cyan]Generating code using OpenAI...[/bold cyan]")

    # Load the OpenAI API key from environment variables
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        console.print("[red]Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.[/red]")
        return None

    full_prompt = f"""
    Here is the current file content:
    {file_contents}

    Task:
    {prompt}

    Please generate the complete, updated file content, including all necessary changes.
    """

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=full_prompt,
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



def refine_and_test_code(generated_code, project_dir):
    console.print("[bold cyan]Refining the generated code using OpenAI...[/bold cyan]")
    prompt = f"""
You are a senior React and Next.js developer.

Review the following generated code. Ensure it is complete, follows best practices, and is ready for production use.

**Important Instructions:**

- **Provide the full, corrected code**: Include all necessary parts without placeholders.
- **No markdown formatting**: Do not include any markdown code fences or formatting symbols.
- **Code only**: Provide only the corrected code without any explanations or additional text.

Generated Code:
{generated_code}

Begin now:
"""
    try:
        refined_code = openai_integration.generate_code(prompt)
        # Save the refined code to the appropriate file
        target_file = os.path.join(project_dir, 'app', 'login', 'page.js')
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(refined_code)

        # Check if npm is available
        npm_path = shutil.which('npm')
        if npm_path is None:
            console.print("[red]Error: 'npm' command not found. Please ensure Node.js and npm are installed and in your PATH.[/red]")
            return None, False

        # Check if 'test' script exists in package.json
        package_json_path = os.path.join(project_dir, 'package.json')
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_json = json.load(f)
        scripts = package_json.get('scripts', {})
        if 'test' in scripts:
            # Run tests
            console.print("[bold cyan]Running tests...[/bold cyan]")
            test_result = subprocess.run([npm_path, 'test'], cwd=project_dir, capture_output=True, text=True)
            if test_result.returncode == 0:
                console.print("[bold green]Tests passed successfully![/bold green]")
                tests_passed = True
            else:
                console.print("[bold red]Tests failed. Output:[/bold red]")
                console.print(test_result.stdout)
                console.print(test_result.stderr)
                tests_passed = False
        else:
            console.print("[yellow]No test script found in package.json. Skipping tests.[/yellow]")
            tests_passed = True  # Assume tests pass if none exist

        return refined_code, tests_passed
    except subprocess.CalledProcessError as e:
        console.print(f"[red]An error occurred while running npm commands: {e}[/red]")
        console.print(e.output)
        return None, False
    except Exception as e:
        console.print(f"[red]Error refining code: {e}[/red]")
        return None, False
