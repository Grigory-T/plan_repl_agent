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


task = """

create doc.txt in CWD
install more itertools
insert some demo code usage for more itertools in doc.txt.

""".strip()

task = """

зверополиз2 мультик
если выстроить всех персонахей по важности
и взять 5ого и 6ого (1ый - самый важный)
назови их имена и краткую характеристику, запиши в doc.txt CWD

""".strip()

print(list_tasks())
run_task(task)
time.sleep(2)
print(list_tasks())