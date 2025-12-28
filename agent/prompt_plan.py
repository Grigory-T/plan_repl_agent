import datetime

PLAN_PROMPT = f"""
current date: {datetime.datetime.now().strftime("%Y-%m-%d")}

Create plan to achieve the following task:

## Task
{{task}}

# Planning instructions
- Break down the task into clear, actionable steps (1-10 steps approximately)
- for simple tasks you can shedule 1-2 step. for complex difficult tasks you can shedule more steps, up to 10

# Input and Output variables
- Each step should contain description and step variables: input_variables and output_variables
- always provide the full explicit information in each step description. Technical details, links, paths, etc.
- input_variables - variables that are used in the step, must me ready before the step execution
- output_variables - variables that are created in the step, must be used in the next steps
- variables names and data types should strictly follow python syntax and types
- do not use `any` type in step_variables
- variables names should not conflict with python built-in variables and keywords
- variable_description should follow the variable_data_type in terms of data type
- use explisit full data types. if needed use nested types (list[tuple[int, str]]).
- e.g. pandas.DataFrame, numpy.ndarray, list[tuple[int, str]], dict[str, list[int]], etc.
- data types should be literal python types in string format.
- first step could not have input_variables (no previous steps to set variables)
- last step could not have output_variables (no next steps to use variables)
- all output variables should be used in the next steps. Do not create unused variables

# Steps could use the following tools:
- python code execution
- bash shell execution
- pip install package_name
- internet (curl, requests etc)
- files system, files read/write, CWD

""".strip()


DECISION_PROMPT = f"""
current date: {datetime.datetime.now().strftime("%Y-%m-%d")}

You are evaluating the progress of a task execution and deciding what to do next.

## Original Task
{{task}}

## Completed Steps
{{completed_steps}}

## Remaining Steps in Plan
{{remaining_steps}}

## Decision Options
- "continue": Move to the next planned step
- "abort": Task cannot be completed, explain why (abort_reason)
- "replan_remaining": when the current plan is not optimal anymore, provide reasons_for_replan_remaining_steps.
- "task completed": when the task is completed successfully, explain why (final_answer)

Rules of replanning:
- when new unexpected information is discovred - `replan_remaining` remaining steps.
- when tasks turns out to be more complex than expected - `replan_remaining` remaining steps.
- when step result are deviating from expected logic of general planning - `replan_remaining` remaining steps.
- if task is followint correct logic in general - `continue` with the plan.
- if `continue` - you should provide `task_continue_reason`, state shortly what was accomplished, and why this is inline with the initial plan.
- aborting is used when:
    task is completed successfully
    critical information is absent and we cannot obtain it using adequate efforts
    critical functionality is absent and we cannot obtain it using adequate efforts
- "task completed": when the task is completed successfully, explain why (final_answer)
- task could be completed successfully without completing all steps, if the steps are not necessary for the task completion (early termination is possible)

""".strip()


REPLAN_REMAINING_PROMPT = f"""
current date: {datetime.datetime.now().strftime("%Y-%m-%d")}

You are replanning the remaining steps of a task based on new information.

## Original Task
{{task}}

## Completed Steps
{{completed_steps}}

## Old Remaining Steps in Plan (to be replaced)
{{remaining_steps}}

## Reasons for replanning remaining steps
{{reasons_for_replan_remaining_steps}}

## Replanning Rules
- you need to provide new remaining steps to complete the task, taking into account what we've learned.
- completed steps cannot be changed. Do not rewrite or copy them.
- when you change the remaining steps, you should take into account the output variables of the completed steps.
- so new steps could take only existing variables from completed steps or new variables that you create in the new steps.
- YOU CAN NOT USE VARIABLES AS INPUT, IF THIS VARIABLE IS NOT SET IN PREVIOUS STEPS.

Important:
- consider radical change in the plan approach, if needed.
- sometimes you need to completely re-think the plan.

""".strip()
