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

install more itertools

""".strip()

# task = """

# зверополиз2 мультик
# если выстроить всех персонахей по важности
# и взять 5ого и 6ого (1ый - самый важный)
# назови их имена и краткую характеристику, запиши в doc.txt CWD

# """.strip()

task = """

создай блюдо на 500 калорий
блюдо должно быть мексиканским, и очень вкусным
найди ингредиенты и их количество для блюда
ну и базовый рецепт сделай, чтобы можно было его приготовить
блюдо должно иметь фиолетовые цвета внутри, хотя бы элементы оформления (это просто моё пожелание)

используй vkusvill_mcp для поиска ингредиентов и рецептов

там все уже готово, просто используй его. Если надо смотри docstrings методов экземпляра vkusvill_mcp.
еще можешь в интернете поискать, если надо.

все результаты опиши кратко в result.md (CWD)
надо еще корзину создать, чтобы можно было купить ингредиенты и приготовить блюдо.
Ссылку на корзину запиши в result.md тоже.

""".strip()

task = """

Твоя задача:
Рассчитай калорийность салата с мандаринами. Одна порция. Ниже полный рецепт.
Результаты запиши в result.md (CWD), калорийность представь по каждому ингредиенту и общее количество калорий.

Рецепт новогоднего салата с мандаринами
Ингредиенты:
Куриное филе — 300 г
Мандарины — 2 шт.
Яблоки — 2 шт.
Яйца — 2 шт.
Листья салата — 3–4 шт.
Лимонный сок — 1 ст. л.
Майонез — 2 ст. л.
Соль и черный молотый перец — по вкусу

""".strip()

task = """

найди все продукты на салат Оливье
выбирай продукты с самым большим рейтингом
результаты - список продуктов с рейтингом и ссылкой на продукт
укажи также цены и общую цену

укажи также, были ли продукты с меньшим рейтингом (чтобы я убедился, что мы именно самый высокий рейтинг выбрали)

"""


task = """

2+2
"""

reset()
clear_directories()

# print(list_tasks())
# print(run_task(task))
# time.sleep(.5)
# print(list_tasks())