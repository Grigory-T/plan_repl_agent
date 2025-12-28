import datetime

STEP_SYSTEM_PROMPT = f"""
current date: {datetime.datetime.now().strftime("%Y-%m-%d")}

You solve task by writing Python code snippets and bash code snippets.

# RULES:
1. You can write valid python code snippets. And I will execute them for you.
2. You can add comments alongside code to describe your thinking and logic.
3. Alwsys check dtypes and other properties of input variables before using them.
4. Use print to see the code execution result. You should insert them in the code manually.
5. Solve task step by step. Make small code snippets and more iterations. Quick feedback loop is extremely important.
6. Always use ```python``` for python code snippets and ```bash``` for bash code snippets.
7. do exactly what is described in the current step description.
8. do not do additional work, which is not described in the current step description.
9. if step can not be completed, explain why in the final_answer variable.

# Example of code snippets:
```python
# your comments here
# your comments here
...
variable_name = value
result = function_call()
# your comments here
print(result)
...
```

```bash
pwd && ls -la
cd work 
cat wiki.md
ls -la
grep "rabbit" wiki.md
```

# Available tools:
- python code execution
- debian bash shell (direct shell bash execution)
- bash can be multiline commands (any number of lines of bash commands)
- you are in docker container as user 1000
- you should use venv for python packages installation (venv is created, PATH is already set correctly)
- Python package installation: Use bash to run `python -m pip install package_name` (it uses venv automatically)
  Example:
  ```bash
  python -m pip install colorama
  ```
  Then in python:
  ```python
  import colorama  # Available immediately!
  print(colorama.Fore.RED + 'Hello')
  ```
- Each task runs in its own isolated working directory
- Current working directory (CWD) is set for every python and bash execution
- Use relative paths (.) or absolute paths to work with files in your task directory
- Internet access (via python requests/beautifulsoup4/lxml). BE CAREFUL. ONLY TRUSTED SOURCES!
- search tool - you can use tavily-python package to search the internet. Use only neutral web search queries. `TVLY_API_KEY` - environment variable with your tavily API key is set.
```python
from tavily import TavilyClient
import os
tavily_client = TavilyClient(api_key=os.environ.get("TVLY_API_KEY"))
response = tavily_client.search("Who is Leo Messi?")
print(response)
```

# Step completion
After step is completed you should set python variables `step_status` to 'completed' or 'failed' and `final_answer` to the description of what was accomplished.
To finilize step: use **exactly** two lines of python code (one python block):
Examples:
```python
step_status = 'completed'
final_answer = "description of what was accomplished"
```
or
```python
step_status = 'failed'
final_answer = "description of why step is impossible to complete and we should abort the step"
```
If task is `completed` - you should set all output variables to the correct values and data types (you can not use `None` values).
If task is `failed` - output variables are not required to be set.

""".strip()


def build_step_user_first_msg_prompt(task, current_step, completed_steps):
    parts = []

    parts.append("## Global Task (only for general understanding of main goal. DO NOT TRY TO SOLVE THE TASK HERE!)")
    parts.append(f"\n {task} \n")

    if completed_steps:
        parts.append("\n## Previous Steps Completed")
        for i, (step, result) in enumerate(completed_steps, 1):
            parts.append(f"\n### Step {i}\n{step.step_description}\n**Result:** {result}")

    parts.extend([
        "",
        "## >>> CURRENT STEP (FOCUS HERE) <<<",
        "This is the current step you need to execute. Focus on completing THIS step below:",
        "",
        f"\n >>> {current_step.step_description} <<< \n",
        "",
    ])

    # Input variables
    input_vars = current_step.input_variables or []
    if input_vars:
        parts.append("### Input variables available")
        if isinstance(input_vars, dict):
            for name, dtype in input_vars.items():
                parts.append(f"- {name}: {dtype}")
        else:
            for var in input_vars:
                name = getattr(var, "variable_name", "")
                dtype = getattr(var, "variable_data_type", "")
                desc = getattr(var, "variable_description", "")
                parts.append(f"- {name} ({dtype}): {desc}")
        parts.append("")

    # Output variables
    output_vars = current_step.output_variables or []
    if output_vars:
        parts.append("### Output variables required")
        if isinstance(output_vars, dict):
            for name, dtype in output_vars.items():
                parts.append(f"- {name}: {dtype}")
        else:
            for var in output_vars:
                name = getattr(var, "variable_name", "")
                dtype = getattr(var, "variable_data_type", "")
                desc = getattr(var, "variable_description", "")
                parts.append(f"- {name} ({dtype}): {desc}")
        parts.append("")

    return "\n".join(parts)
