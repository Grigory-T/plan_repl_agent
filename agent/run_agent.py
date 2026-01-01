from .plan import (
    AfterStepDecision,
    Plan,
    PlanStep,
    create_plan,
    make_after_step_decision,
    replan_remaining,
)
from .run_step import run_step
from .executor import execute_python
from .log import _init_log_dir, _append_log, _format_plan


MAX_TOTAL_STEPS = 30


def run_agent(task: str, log_dir_name: str | None = None) -> str:
    log_dir = _init_log_dir(log_dir_name)
    plan: Plan = create_plan(task)
    remaining_steps: list[PlanStep] = list(plan.steps)
    completed_steps: list[tuple[PlanStep, str]] = []
    _append_log(log_dir / "plan.txt", "Initial plan:\n" + _format_plan(plan))

    for _ in range(MAX_TOTAL_STEPS):
        if not remaining_steps:
            break

        current_step = remaining_steps.pop(0)
        step_number = len(completed_steps) + 1
        
        execute_python("final_answer = ''")

        step_result = run_step(
            task=task,
            current_step=current_step,
            completed_steps=completed_steps,
            log_dir=log_dir,
            step_index=step_number,
        )
        completed_steps.append((current_step, step_result))

        decision: AfterStepDecision = make_after_step_decision(
            task=task,
            completed_steps=completed_steps,
            remaining_steps=remaining_steps,
        )
        _append_log(
            log_dir / "decisions.txt",
            f"Decision after step {step_number}:\n{decision.model_dump_json(indent=2)}",
        )

        if decision.next_action == "abort":
            return decision.abort_reason or "Aborted by decision"

        if decision.next_action == 'task_completed':
            return decision.task_completed_reason

        if decision.next_action == "replan_remaining_steps":
            plan = replan_remaining(
                task=task,
                completed_steps=completed_steps,
                remaining_steps=remaining_steps,
                after_step_decision=decision,
            )
            remaining_steps = list(plan.steps)
            _append_log(
                log_dir / "plan.txt",
                f"Replan after step {step_number}:\n" + _format_plan(plan, start_step=step_number + 1),
            )

    if remaining_steps:
        return "Stopped: exceeded max total steps."

    return completed_steps[-1][1]
