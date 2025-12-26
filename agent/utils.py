import os
import json
import ast
from typing import Literal, List
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

def _env_str(name: str, default: str) -> str:
    """Return env var value if set and non-empty, otherwise a default."""
    val = os.getenv(name)
    return val if val else default


LLM_MODEL_PLAN = _env_str("LLM_MODEL_PLAN", "openai/gpt-4.1")
LLM_MODEL_DECISION = _env_str("LLM_MODEL_DECISION", "openai/gpt-4.1")
LLM_MODEL_REPLAN = _env_str("LLM_MODEL_REPLAN", "openai/gpt-4.1")

LLM_MODEL_AGENT = _env_str("LLM_MODEL_AGENT", "deepseek/deepseek-v3.2")

def llm_structured(prompt: str, response_model: type[BaseModel], model: str | None = None) -> BaseModel:
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    schema = response_model.model_json_schema()
    req = json.dumps(schema, ensure_ascii=False)
    full = f"{prompt}\n\nReturn only JSON matching this: {req}"
    resp = client.chat.completions.create(
        model=model or LLM_MODEL_PLAN,
        messages=[{"role": "user", "content": full}],
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "response_schema",
                "strict": False,
                "schema": schema
            }
        },
        max_tokens=5_000,
    )
    content = resp.choices[0].message.content
    return response_model.model_validate_json(content)



def llm(messages: list, model: str | None = None) -> tuple[str, str]:
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    
    resp = client.chat.completions.create(
        model=model or LLM_MODEL_AGENT,
        messages=messages,
        temperature=0,
        max_tokens=10_000,
        # stop=['```\n'],
        extra_body={
            "reasoning": {
                "effort": "minimal"  #  "minimal", "low", "medium", "high", "xhigh"
            }
        }
    )
    
    message = resp.choices[0].message
    content = message.content

    # Keep only first code block (bash/python) if present, otherwise keep all text
    # first_block_start = content.find("```")
    # if first_block_start != -1:
    #     first_block_end = content.find("```", first_block_start + 3)
    #     if first_block_end != -1:
    #         content = content[:first_block_end + 3]

    class ResponseBlock(BaseModel):
        block_id: int
        block_type: Literal["python", "bash", "text"]
        block_text: str

    blocks: list[ResponseBlock] = []

    # Parse content into ordered blocks, removing ``` fences but preserving sequence.
    # We do NOT modify inner text/code; only strip the fence markers.
    idx = 0
    block_idx = 0
    while True:
        start = content.find("```", idx)
        if start == -1:
            # Remaining text
            tail = content[idx:]
            if tail:
                blocks.append(ResponseBlock(block_id=block_idx, block_type="text", block_text=tail))
                block_idx += 1
            break

        # Text before fence
        if start > idx:
            text_part = content[idx:start]
            blocks.append(ResponseBlock(block_id=block_idx, block_type="text", block_text=text_part))
            block_idx += 1

        # Determine block type from fence
        lang_end = content.find("\n", start + 3)
        if lang_end == -1:
            lang_end = start + 3
        lang = content[start + 3:lang_end].strip()
        block_type = "text"
        if lang == "python":
            block_type = "python"
        elif lang == "bash":
            block_type = "bash"

        # Find closing fence
        close = content.find("```", lang_end)
        if close == -1:
            code_part = content[lang_end:]
            idx = len(content)
        else:
            code_part = content[lang_end:close]
            idx = close + 3

        blocks.append(ResponseBlock(block_id=block_idx, block_type=block_type, block_text=code_part))
        block_idx += 1

    reasoning = ''
    reasoning_details = getattr(message, 'reasoning_details', None)
    if reasoning_details:
        reasoning_parts = []
        for detail in reasoning_details:
            if detail.get('type') == 'reasoning.text':
                reasoning_parts.append(detail.get('text', ''))
            elif detail.get('type') == 'reasoning.summary':
                reasoning_parts.append(detail.get('summary', ''))
        reasoning = '\n\n'.join(reasoning_parts)
    
    return content, blocks, reasoning.strip()


def check_assigned_variables(code: str) -> bool:
    """Check if final_answer or step_status is assigned in the code string."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("final_answer", "step_status"):
                        return True
                    if isinstance(target, (ast.Tuple, ast.List)):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name) and elt.id in ("final_answer", "step_status"):
                                return True
        return False
    except Exception:
        return False


def format_step_variables(variables: List) -> str:
    """Format list of StepVariable objects into readable string."""
    if not variables:
        return "None"
    
    lines = []
    for var in variables:
        lines.append(f"  - {var.variable_name} ({var.variable_data_type}): {var.variable_description}")
    
    return "\n" + "\n".join(lines)


