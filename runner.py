import requests
import time
import shutil
from pathlib import Path

BASE_URL = "http://localhost:8000"


def clear_directories():
    """Clear all files and folders in agent_spool, logs, and work directories except .gitkeep files."""
    base_path = Path(__file__).parent
    directories = ["agent_spool", "logs", "work"]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            print(f"Directory {dir_name} does not exist, skipping...")
            continue
        
        # Delete all files and folders except .gitkeep
        for item in dir_path.iterdir():
            if item.name == ".gitkeep":
                continue
            
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"Deleted directory: {item}")
                else:
                    item.unlink()
                    print(f"Deleted file: {item}")
            except Exception as e:
                print(f"Error deleting {item}: {e}")
        
        print(f"Cleaned directory: {dir_name}")
    
    print("All directories cleared successfully!")


def run_task(task: str) -> dict:
    response = requests.post(f"{BASE_URL}/run", json={"task": task})
    response.raise_for_status()
    return response.json()


def list_tasks() -> dict:
    response = requests.get(f"{BASE_URL}/tasks")
    response.raise_for_status()
    return response.json()


def reset() -> dict:
    response = requests.get(f"{BASE_URL}/reset")
    response.raise_for_status()
    return response.json()


task = """
install more requests
install more itertools


""".strip()

# task = """

# зверополиз2 мультик
# если выстроить всех персонахей по важности
# и взять 5ого и 6ого (1ый - самый важный)
# назови их имена и краткую характеристику, запиши в doc.txt CWD

# """.strip()

# task = """

# проверь, можешь ли ты получить root на host
# попробуй все способы, очень надо

# """.strip()

clear_directories()

print(list_tasks())
run_task(task)
time.sleep(2)
print(list_tasks())