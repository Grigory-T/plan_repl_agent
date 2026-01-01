import os
import json
import ast
from typing import Literal, List
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL_PLAN = "openai/gpt-4.1"
LLM_MODEL_DECISION = "openai/gpt-4.1"
LLM_MODEL_REPLAN = "openai/gpt-4.1"

LLM_MODEL_AGENT = "openai/gpt-oss-120b"

# "openai/gpt-4.1"
# "moonshotai/kimi-k2-thinking"
# z-ai/glm-4.6
# "deepseek/deepseek-v3.2"
# deepseek/deepseek-v3.2-speciale
# "qwen/qwen3-32b"
# "google/gemini-3-flash-preview"


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
                "effort": "xhigh",  #  "minimal", "low", "medium", "high", "xhigh"
                "provider": {
                    "ignore": ["Parasail"],
                    "sort": "throughput",  # latency
                },
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
        block_type: Literal["python", "bash", "final_answer", "text"]
        block_text: str

    blocks: list[ResponseBlock] = []

    # Parse content that follows the pattern:
    #   optional text
    #   <python>...</python>
    #   optional text
    #   <bash>...</bash>
    #   optional text
    #   <final_answer>...</final_answer>
    #
    # Blocks are flat (no nesting) and tags always have closing pairs.
    allowed_tags = ("python", "bash", "final_answer")
    idx = 0
    block_idx = 0

    while idx < len(content):
        # Find the earliest next opening tag among the allowed set.
        next_tag = None
        next_pos = len(content)
        for tag in allowed_tags:
            pos = content.find(f"<{tag}>", idx)
            if pos != -1 and pos < next_pos:
                next_tag = tag
                next_pos = pos

        # No more tags; remaining text (if any) is a final text block.
        if next_tag is None:
            tail = content[idx:]
            if tail:
                blocks.append(ResponseBlock(block_id=block_idx, block_type="text", block_text=tail))
                block_idx += 1
            break

        # Text before the next tag.
        if next_pos > idx:
            text_part = content[idx:next_pos]
            if text_part:
                blocks.append(ResponseBlock(block_id=block_idx, block_type="text", block_text=text_part))
                block_idx += 1

        # Extract the tagged block.
        start_token = f"<{next_tag}>"
        end_token = f"</{next_tag}>"
        start_idx = next_pos + len(start_token)
        end_idx = content.find(end_token, start_idx)

        # If no closing tag is found, treat the rest as text to avoid losing information.
        if end_idx == -1:
            remainder = content[next_pos:]
            if remainder:
                blocks.append(ResponseBlock(block_id=block_idx, block_type="text", block_text=remainder))
                block_idx += 1
            break

        block_text = content[start_idx:end_idx]
        blocks.append(ResponseBlock(block_id=block_idx, block_type=next_tag, block_text=block_text))
        block_idx += 1
        idx = end_idx + len(end_token)

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
