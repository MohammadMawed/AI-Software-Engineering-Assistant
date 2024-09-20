import sqlite3
import json
from rich.console import Console
from rich.table import Table
from collections import defaultdict

console = Console()

DATABASE_FILE = 'ai_assistant.db'

def get_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def evaluate_ai_performance():
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all requests and their associated code generations
    cursor.execute('''
        SELECT r.id, r.human_request, r.task_description, 
               c.version, c.generated_content,
               rl.state, rl.action, rl.reward
        FROM Requests r
        LEFT JOIN CodeGenerations c ON r.id = c.request_id
        LEFT JOIN RLData rl ON r.id = rl.request_id
        ORDER BY r.id, c.version
    ''')

    results = cursor.fetchall()
    conn.close()

    performance_data = defaultdict(list)
    for row in results:
        request_id = row['id']
        performance_data[request_id].append({
            'human_request': row['human_request'],
            'task_description': row['task_description'],
            'version': row['version'],
            'generated_content': row['generated_content'],
            'state': json.loads(row['state']) if row['state'] else None,
            'action': row['action'],
            'reward': row['reward']
        })

    return performance_data

def analyze_performance(performance_data):
    total_requests = len(performance_data)
    successful_implementations = 0
    total_versions = 0
    total_reward = 0
    action_counts = defaultdict(int)

    for request_id, versions in performance_data.items():
        total_versions += len(versions)
        last_version = versions[-1]
        
        # Check if reward is not None before comparison
        if last_version['reward'] is not None and last_version['reward'] > 0:
            successful_implementations += 1
        
        # Sum up rewards, ignoring None values
        total_reward += sum(v['reward'] for v in versions if v['reward'] is not None)
        
        for v in versions:
            if v['action']:
                action_counts[v['action']] += 1

    avg_versions_per_request = total_versions / total_requests if total_requests > 0 else 0
    success_rate = (successful_implementations / total_requests) * 100 if total_requests > 0 else 0
    avg_reward = total_reward / total_versions if total_versions > 0 else 0

    return {
        'total_requests': total_requests,
        'successful_implementations': successful_implementations,
        'avg_versions_per_request': avg_versions_per_request,
        'success_rate': success_rate,
        'avg_reward': avg_reward,
        'action_counts': action_counts
    }
   
def print_performance_results(analysis):
    console.print("[bold]AI Agent Performance Evaluation[/bold]", style="cyan")
    console.print(f"Total Requests Processed: {analysis['total_requests']}")
    console.print(f"Successful Implementations: {analysis['successful_implementations']}")
    console.print(f"Average Versions per Request: {analysis['avg_versions_per_request']:.2f}")
    console.print(f"Success Rate: {analysis['success_rate']:.2f}%")
    console.print(f"Average Reward: {analysis['avg_reward']:.2f}")

    console.print("\n[bold]Action Distribution:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Action", style="dim", width=12)
    table.add_column("Count", justify="right")
    table.add_column("Percentage", justify="right")

    total_actions = sum(analysis['action_counts'].values())
    for action, count in analysis['action_counts'].items():
        percentage = (count / total_actions) * 100 if total_actions > 0 else 0
        table.add_row(action, str(count), f"{percentage:.2f}%")

    console.print(table)

if __name__ == "__main__":
    performance_data = evaluate_ai_performance()
    analysis = analyze_performance(performance_data)
    print_performance_results(analysis)