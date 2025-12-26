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
    path = Path(filepath)
    if not path.exists():
        print(f"Error: Task file '{filepath}' not found.")
        sys.exit(1)
    return path.read_text(encoding='utf-8').strip()


# Default task for backward compatibility
test = """you task is to try out tool FTA (Flat Table Analysis) and state you opinion about it (in report.md file, CWD)
download any table to test, any table with interesting relations between columns

# FTA code example:
!pip install flattableanalysis
from flattableanalysis.flat_table_analysis import FlatTableAnalysis
df = pd.DataFrame(YOUR_DATA)
fta = FlatTableAnalysis(df)  # create analysis object
fta.get_candidate_keys(2)  # check 2-cols candidates
fta.show_fd_graph()[0]  # see graph of functional dependencies (all pairs of columns)

you can use CWD folder to store files and data, if needed."""


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
