import ast
from pathlib import Path
from typeguard import check_type

from .utils import llm, LLM_MODEL_AGENT, check_assigned_variables, format_step_variables
from .prompt_agent import STEP_SYSTEM_PROMPT, build_step_user_first_msg_prompt
from .executor import execute_python, execute_bash, PERSISTENT_GLOBALS
from .log import _append_step_log, _append_reasoning

MAX_ITERATIONS_PER_STEP = 30

def run_step(task, current_step, completed_steps, log_dir=None, step_index=0) -> str:
    step_folder = Path(log_dir) / f"step_{step_index}" if log_dir else None
    messages_log = step_folder / "messages.txt" if step_folder else None
    reasoning_log = step_folder / "reasoning.txt" if step_folder else None

    system_prompt = STEP_SYSTEM_PROMPT
    user_prompt = build_step_user_first_msg_prompt(
        task=task,
        current_step=current_step,
        completed_steps=completed_steps,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    _append_step_log(messages_log, "system", system_prompt)
    _append_step_log(messages_log, "user", user_prompt)

    for _ in range(MAX_ITERATIONS_PER_STEP):
        llm_response, llm_response_blocks, reasoning = llm(messages, model=LLM_MODEL_AGENT)

        if not llm_response_blocks:
            continue
        
        _append_reasoning(reasoning_log, reasoning)

        has_code_blocks = any(block.block_type in ("python", "bash") for block in llm_response_blocks)
        has_final_blocks = any(block.block_type == "final_answer" for block in llm_response_blocks)
        only_text_blocks = all(block.block_type == "text" for block in llm_response_blocks)

        # Case 1: only text - ask LLM to produce runnable code.
        if only_text_blocks:
            if llm_response and llm_response.strip():
                messages.append({"role": "assistant", "content": llm_response})
                _append_step_log(messages_log, "assistant", llm_response)
            user_msg = (
                "No valid code to execute. Respond with <python>...</python> or <bash>...</bash> blocks to run code.\n"
                "When the step is finished, you must return a <final_answer>...</final_answer> block that sets exactly two variables:\n"
                "step_status = 'completed' or 'failed'\n"
                "final_answer = 'short description of the result'"
            )
            messages.append({"role": "user", "content": user_msg})
            _append_step_log(messages_log, "user", user_msg)
            continue

        # Case 2: python/bash present (ignore any final_answer blocks while running code).
        if has_code_blocks:
            if has_final_blocks:
                llm_response_blocks = [b for b in llm_response_blocks if b.block_type != "final_answer"]

            pending_text = []
            pair_idx = 0  # numbering for code/result pairs in logs

            for block in llm_response_blocks:
                if block.block_type == "text":
                    if block.block_text and block.block_text.strip():
                        pending_text.append(block.block_text)
                    continue

                if block.block_type not in ("python", "bash"):
                    continue

                code_type = block.block_type
                code = block.block_text

                assistant_msg = "".join(pending_text) + f"<{code_type}>\n{code}\n</{code_type}>"
                pending_text = []
                messages.append({"role": "assistant", "content": assistant_msg})
                _append_step_log(messages_log, f"assistant {pair_idx}", assistant_msg)

                if code_type == "python":
                    code_response = execute_python(code)
                elif code_type == "bash":
                    code_response = execute_bash(code)
                else:
                    user_msg = f"Unknown code type: {code_type}"
                    messages.append({"role": "user", "content": user_msg})
                    _append_step_log(messages_log, "user", user_msg)
                    continue

                result_parts = []
                if code_response.stdout:
                    result_parts.append(f"\n**STDOUT:**\n{code_response.stdout}")
                if code_response.stderr:
                    result_parts.append(f"**STDERR:**\n{code_response.stderr}")
                block_result = "Code execution result:\n" + "\n\n".join(result_parts) if result_parts else "Code execution result: (no output)"

                messages.append({"role": "user", "content": block_result})
                _append_step_log(messages_log, f"user {pair_idx}", block_result)
                pair_idx += 1

            if pending_text:
                text_msg = "".join(pending_text)
                if text_msg.strip():
                    messages.append({"role": "assistant", "content": text_msg})
                    _append_step_log(messages_log, "assistant", text_msg)

            continue

        # Case 3: only final_answer blocks (no python/bash). Validate format and data types.
        if has_final_blocks:
            if llm_response and llm_response.strip():
                messages.append({"role": "assistant", "content": llm_response})
                _append_step_log(messages_log, "assistant", llm_response)

            final_blocks = [b for b in llm_response_blocks if b.block_type == "final_answer"]
            if len(final_blocks) != 1:
                fix_msg = (
                    "Provide exactly one <final_answer> block that contains python assigning `step_status` ('completed' or 'failed') and `final_answer` (description)."
                )
                messages.append({"role": "user", "content": fix_msg})
                _append_step_log(messages_log, "user", fix_msg)
                continue

            final_code = final_blocks[0].block_text

            try:
                parsed = ast.parse(final_code)
            except Exception:
                fix_msg = (
                    "The <final_answer> block must be valid python that sets `step_status` ('completed' or 'failed') and `final_answer` (description). "
                    "Please resend a <final_answer> block with exactly those assignments."
                )
                messages.append({"role": "user", "content": fix_msg})
                _append_step_log(messages_log, "user", fix_msg)
                continue

            # Enforce structure: exactly two assignments to step_status and final_answer, nothing else.
            valid_structure = False
            if len(parsed.body) == 2 and all(isinstance(stmt, ast.Assign) for stmt in parsed.body):
                targets = []
                for stmt in parsed.body:
                    for t in stmt.targets:
                        if isinstance(t, (ast.Tuple, ast.List)):
                            targets.extend([elt.id for elt in t.elts if isinstance(elt, ast.Name)])
                        elif isinstance(t, ast.Name):
                            targets.append(t.id)
                valid_structure = sorted(targets) == ["final_answer", "step_status"]

            if not valid_structure:
                fix_msg = (
                    "The <final_answer> block must contain exactly two assignment statements: one to `step_status` and one to `final_answer`, and nothing else."
                )
                messages.append({"role": "user", "content": fix_msg})
                _append_step_log(messages_log, "user", fix_msg)
                continue

            execute_python(final_code)

            final_answer = PERSISTENT_GLOBALS.get('final_answer', '')
            step_status = PERSISTENT_GLOBALS.get('step_status', '')

            if step_status not in ('completed', 'failed') or not final_answer:
                fix_msg = (
                    "Ensure <final_answer> sets both variables exactly:\n"
                    "step_status = 'completed' or 'failed'\n"
                    "final_answer = 'description of the result'"
                )
                messages.append({"role": "user", "content": fix_msg})
                _append_step_log(messages_log, "user", fix_msg)
                continue

            if step_status == 'failed':
                return final_answer

            error_msg = ""
            for var in current_step.output_variables:
                name = var.variable_name
                dtype_str = var.variable_data_type
                value = PERSISTENT_GLOBALS.get(name, None)
                if value is None:
                    error_msg += f'Missing variable: {name}\n'
                else:
                    if dtype_str == 'object':
                        continue
                    try:
                        glbs = dict(PERSISTENT_GLOBALS)
                        if 'pd' in glbs and 'pandas' not in glbs:
                            glbs['pandas'] = glbs['pd']
                        if 'np' in glbs and 'numpy' not in glbs:
                            glbs['numpy'] = glbs['np']
                        
                        dtype = eval(dtype_str, glbs)
                        check_type(value, dtype)
                    except Exception as e:
                        error_msg += (f'Error: {name} is {type(value).__name__} but expected literal python type: {dtype_str}\n'
                                        f'make sure that the variable {dtype_str} class exists verbatim in current python environment.\n'
                                        f'name of the class should be verbatim {dtype_str}, so re-import it if needed\n'
                                        f'examples of different imports: import pandas as pd VS import pandas; import numpy as np VS import numpy; etc\n'
                                        )

            if error_msg:
                messages.append({"role": "user", "content": error_msg})
                _append_step_log(messages_log, "user", error_msg)
                continue

            return final_answer

    return "Max iterations reached without a final answer."
