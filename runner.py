import requests
import time
import sys
import argparse
from typing import Optional
from pathlib import Path

BASE_URL = "http://localhost:8000"


def run_task(task: str) -> dict:
    """Run a task on the agent server."""
    response = requests.post(f"{BASE_URL}/run", json={"task": task})
    response.raise_for_status()
    return response.json()


def list_tasks() -> dict:
    """List all tasks from the agent server."""
    response = requests.get(f"{BASE_URL}/tasks")
    response.raise_for_status()
    return response.json()


def reset() -> dict:
    """Reset the agent server."""
    response = requests.get(f"{BASE_URL}/reset")
    response.raise_for_status()
    return response.json()


def load_task_from_file(filepath: str) -> str:
    """Load task text from file."""
    path = Path(__file__).parent / "tasks" / filepath
    if not path.exists():
        print(f"Error: Task file '{filepath}' not found.")
        sys.exit(1)
    return path.read_text(encoding='utf-8').strip()


# Default task for backward compatibility
test = """create doc.txt in CWD"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run agent task')
    parser.add_argument('-i', '--input', type=str, help='Task file path')
    args = parser.parse_args()
    
    if args.input:
        task = load_task_from_file(args.input)
    else:
        print("Use -i <task_file> to specify a task file. Running default task.")
        task = test
    
    run_task(task)
    time.sleep(0.5)
    print(list_tasks())
