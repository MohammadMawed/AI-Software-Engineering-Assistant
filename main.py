import re
import os
import logging
import traceback
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import json
import subprocess
import glob
import chardet

# Import database and RL agent functions
from database import setup_database, insert_request, insert_code_generation, insert_rl_data
from rl_agent import RLAgent
from reward_calculation import calculate_reward

# Set up logging
logging.basicConfig(filename='ai_assistant.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  # Load environment variables from .env file
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
console = Console()

def log_and_print(message, level='info'):
    console.print(message)
    if level == 'info':
        logging.info(message)
    elif level == 'error':
        logging.error(message)

def save_data(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)

def find_relevant_files(project_dir, task_description):
    js_files = glob.glob(os.path.join(project_dir, '**', '*.js'), recursive=True)
    jsx_files = glob.glob(os.path.join(project_dir, '**', '*.jsx'), recursive=True)
    all_files = js_files + jsx_files
    
    for file in all_files:
        try:
            with open(file, 'rb') as f:
                raw_content = f.read()
            detected = chardet.detect(raw_content)
            encoding = detected['encoding']
            
            content = raw_content.decode(encoding)
            
            if 'password' in content.lower() and 'input' in content.lower():
                return file
        except Exception as e:
            log_and_print(f"[yellow]Warning: Could not read file {file}. Error: {e}[/yellow]", 'info')
    
    return all_files[0] if all_files else None

def display_file_content(file_path):
    try:
        with open(file_path, 'rb') as file:
            raw_content = file.read()
        detected = chardet.detect(raw_content)
        encoding = detected['encoding']
        content = raw_content.decode(encoding)
        syntax = Syntax(content, "javascript", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"Content of {os.path.basename(file_path)}", expand=False))
    except Exception as e:
        log_and_print(f"[bold red]Error displaying file content: {e}[/bold red]", 'error')

def validate_nextjs_code(code):
    issues = []
    
    if '"use client";' not in code and "'use client';" not in code:
        if any(hook in code for hook in ['useState', 'useEffect', 'useRouter']):
            issues.append("Client-side hooks are used without 'use client' directive")

    if 'useRouter' in code:
        if 'import { useRouter } from "next/navigation";' not in code and "import { useRouter } from 'next/navigation';" not in code:
            issues.append("useRouter is imported incorrectly. It should be imported from 'next/navigation'")
        
        router_usage = re.search(r'const\s+\w+\s*=\s*useRouter\(\)', code)
        if router_usage:
            component_def = re.search(r'(function|const)\s+\w+\s*=?\s*(\(|\{)', code[:router_usage.start()])
            if not component_def:
                issues.append("useRouter should be used inside a component function, not at the top level")

    if 'router.push(' in code:
        issues.append("router.push() is used. Consider using the Link component for client-side navigation instead")

    if re.search(r'router\.\w+\([^)]*\)', code) and 'const router = useRouter()' not in code:
        issues.append("router is used before it's defined with useRouter()")

    return issues

def post_process_nextjs_code(code):
    if any(hook in code for hook in ['useState', 'useEffect', 'useRouter']):
        if not code.startswith('"use client";') and not code.startswith("'use client';"):
            code = '"use client";\n\n' + code

    code = code.replace('import { useRouter } from "next/router";', 'import { useRouter } from "next/navigation";')
    code = code.replace("import { useRouter } from 'next/router';", "import { useRouter from 'next/navigation';")

    code = re.sub(r'router\.push\([\'"](.+?)[\'"]\)', r'<Link href="\1">Navigate</Link>', code)

    return code

def generate_complete_code(task_description, file_content):
    console.print("[bold cyan]Generating complete code using OpenAI...[/bold cyan]")
    prompt = f"""
You are a proficient React and Next.js developer, specifically for Next.js version 13 and above.

Task: {task_description}

Current file content:
{file_content}

Please generate the complete, updated file content implementing the requested feature.

**Important Instructions:**

- Ensure the code follows Next.js 13+ best practices.
- Use the 'use client' directive at the top of the file if any client-side hooks (useState, useEffect, useRouter) are used.
- Import useRouter from 'next/navigation', not 'next/router'.
- Use the Link component from 'next/link' for navigation instead of router.push().
- Avoid using useRouter or other client-side hooks at the top level of the file. They should be used inside component functions.
- Provide the full code, including all necessary imports, component definitions, and the full implementation.
- Do not use placeholders or comments like "// rest of the code goes here".
- Do not include any markdown formatting or formatting symbols in your response.
- Provide only the code without any explanations or additional text.

Begin now:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0
        )
        generated_code = response.choices[0].message.content.strip()
        return post_process_nextjs_code(generated_code)
    except Exception as e:
        log_and_print(f"[bold red]Error generating code: {e}[/bold red]", 'error')
        return None

def save_code_to_file(code, target_file):
    console.print("[bold cyan]Saving code to file...[/bold cyan]")
    try:
        with open(target_file, 'w', encoding='utf-8') as file:
            file.write(code)
        console.print(f"[green]Code saved to {target_file}[/green]")
        return True
    except Exception as e:
        log_and_print(f"[bold red]Error saving code to file: {e}[/bold red]", 'error')
        return False

def run_tests(project_dir):
    console.print("[bold cyan]Running tests...[/bold cyan]")
    try:
        result = subprocess.run(['npm', 'test'], cwd=project_dir, capture_output=True, text=True)
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, f"An error occurred while running tests: {e}"

def run_linter(project_dir):
    console.print("[bold cyan]Running linter...[/bold cyan]")
    try:
        result = subprocess.run(['npx', 'eslint', '.'], cwd=project_dir, capture_output=True, text=True)
        return result.stdout.count('error'), result.stdout
    except Exception as e:
        return -1, f"An error occurred while running linter: {e}"

def log_original_code(file_path, content):
    log_entry = f"""
    Original code in {file_path}:
    ```javascript
    {content}
    ```
    """
    logging.info(log_entry)
    console.print("[bold green]Original code logged successfully.[/bold green]")

def main():
    # Setup the SQLite database
    setup_database()

    # Initialize RL Agent
    actions = ['proceed', 'modify', 'regenerate']
    agent = RLAgent(actions)

    console.print(Panel.fit("[bold cyan]Welcome to the AI Assistant![/bold cyan]\n"
                            "I'm here to help you implement new features in your project.",
                            title="AI Assistant", border_style="cyan"))
    
    project_dir = console.input("[bold cyan]Enter the path to your project folder: [/bold cyan]")
    
    while not os.path.exists(project_dir):
        console.print("[bold red]The specified directory does not exist.[/bold red]")
        project_dir = console.input("[bold cyan]Please enter a valid project folder path: [/bold cyan]")
    
    task_description = console.input("[bold cyan]Describe the feature you want to implement: [/bold cyan]")
    
    log_and_print(f"Project directory: {project_dir}")
    log_and_print(f"Task description: {task_description}")

    # Save inputs for future reference
    save_data({'project_dir': project_dir, 'task_description': task_description}, 'task_info.json')

    # Find relevant file and display content
    relevant_file = find_relevant_files(project_dir, task_description)
    if relevant_file:
        log_and_print(f"[bold green]Relevant file found: {relevant_file}[/bold green]")
        display_file_content(relevant_file)
    else:
        log_and_print("[bold yellow]No relevant file found. A new file will be created.[/bold yellow]")
        relevant_file = os.path.join(project_dir, 'components', 'PasswordInput.js')

    try:
        # Read existing file content or use an empty string for new files
        file_content = open(relevant_file, 'r', encoding='utf-8').read() if os.path.exists(relevant_file) else ""

        # Log the original code
        log_original_code(relevant_file, file_content)

        # Insert request into database
        request_id = insert_request(human_request=task_description, task_description=task_description, 
                                    file_path=relevant_file, original_content=file_content)

        # Generate complete code using OpenAI
        generated_code = generate_complete_code(task_description, file_content)

        if generated_code:
            console.print(Panel(Syntax(generated_code, "javascript", theme="monokai", line_numbers=True), 
                                title="Generated Code", expand=False))

            # Validate Next.js specific issues
            nextjs_issues = validate_nextjs_code(generated_code)
            if nextjs_issues:
                console.print("[bold yellow]Potential Next.js issues detected:[/bold yellow]")
                for issue in nextjs_issues:
                    console.print(f"- {issue}")
                
                # Ask if the user wants to regenerate the code
                regenerate = console.input("[bold cyan]Do you want to regenerate the code? (yes/no): [/bold cyan]").lower()
                if regenerate == 'yes':
                    generated_code = generate_complete_code(task_description, file_content)
                    console.print(Panel(Syntax(generated_code, "javascript", theme="monokai", line_numbers=True), 
                                        title="Regenerated Code", expand=False))
            else:
                console.print("[bold green]No obvious Next.js issues detected.[/bold green]")

            # Save generated code to file
            if save_code_to_file(generated_code, relevant_file):
                console.print("[bold green]Code has been successfully generated and saved.[/bold green]")
                
                # Run tests and linter
                tests_passed, test_output = run_tests(project_dir)
                lint_errors, lint_output = run_linter(project_dir)

                if tests_passed:
                    console.print("[bold green]Tests passed successfully![/bold green]")
                else:
                    console.print("[bold red]Tests failed. Output:[/bold red]")
                    console.print(test_output)

                if lint_errors == 0:
                    console.print("[bold green]No linting errors found.[/bold green]")
                else:
                    console.print(f"[bold yellow]{lint_errors} linting errors found. Please review the code.[/bold yellow]")

                # RL Agent decision-making and reward calculation
                code_quality_metrics = [int(tests_passed), lint_errors]
                state = agent.get_state(code_quality_metrics, True)  # Assuming comparison result is True for now
                action = agent.choose_action(state)
                reward = calculate_reward(tests_passed, lint_errors, True)  # Assuming comparison_result is True
                next_state = agent.get_state(code_quality_metrics, True)  # Update based on actual task progress

                # Insert RL data into the database
                insert_rl_data(request_id, state, action, reward, next_state)

                # Agent learns from experience
                agent.learn(state, action, reward, next_state)
                agent.save_q_table()

                console.print(f"[bold cyan]Reward for this implementation: {reward}[/bold cyan]")

            else:
                console.print("[bold red]Failed to save the generated code. Please check file permissions and try again.[/bold red]")
        else:
            log_and_print("[bold red]Failed to generate code. Exiting.[/bold red]", 'error')

    except Exception as e:
        log_and_print(f"[bold red]An unexpected error occurred: {e}[/bold red]", 'error')
        log_and_print(traceback.format_exc(), 'error')

    console.print(Panel.fit("[bold cyan]Thank you for using the AI Assistant![/bold cyan]\n"
                            "I hope I was helpful in implementing your feature.",
                            title="Goodbye", border_style="cyan"))

if __name__ == "__main__":
    main()