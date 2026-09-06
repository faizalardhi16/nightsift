"""repair node: bounded repair loop (PRD sections 51-53)."""

from __future__ import annotations

from nightshift.app.coding.base import CodingRequest
from nightshift.app.coding.registry import get_agent
from nightshift.app.config.logging import get_logger
from nightshift.app.persistence.models import RepairAttempt
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


def build_repair_prompt(ctx: WorkflowContext) -> str:
    """Assemble context-rich repair prompt (PRD section 52)."""
    task = ctx.get("task", {})
    validation = ctx.get("validation_result", {})
    attempt = ctx.execution.repair_attempt + 1

    return (
        "Your previous implementation failed validation. Fix it.\n\n"
        f"ORIGINAL TASK:\n{task.get('title')}\n{task.get('description')}\n\n"
        f"VALIDATION FAILURES:\n{validation}\n\n"
        f"REPAIR ATTEMPT: {attempt}\n\n"
        "Keep changes minimal and targeted. Fix only what failed. "
        "Do not introduce unrelated changes."
    )


async def repair(ctx: WorkflowContext) -> State:
    workspace_path = ctx.get("workspace_path")
    repository = ctx.get("repository", {})

    ctx.execution.repair_attempt += 1
    attempt = ctx.execution.repair_attempt
    logger.info("repair_attempt", attempt=attempt)

    if attempt > ctx.settings.max_repair_attempts:
        return State.BLOCKED

    prompt = build_repair_prompt(ctx)

    agent_name = (
        (ctx.get("context", {}).get("repo_config", {}).get("coding", {}) or {}).get(
            "default_agent"
        )
        or ctx.settings.default_coding_agent
    )

    request = CodingRequest(
        task_id=ctx.execution.external_task_id,
        repository_path=repository.get("local_path", ""),
        workspace_path=workspace_path or "",
        prompt=prompt,
        timeout_seconds=ctx.settings.coding_timeout_seconds,
    )

    try:
        agent = get_agent(agent_name)
        result = await agent.execute(request)
    except Exception as exc:
        logger.error("repair_agent_failed", error=str(exc))
        ctx.session.add(
            RepairAttempt(
                task_execution_id=ctx.execution_id,
                attempt=attempt,
                prompt=prompt,
                success=False,
                failure_analysis={"error": str(exc)},
            )
        )
        ctx.session.flush()
        return State.VALIDATING if attempt < ctx.settings.max_repair_attempts else State.BLOCKED

    ctx.session.add(
        RepairAttempt(
            task_execution_id=ctx.execution_id,
            attempt=attempt,
            prompt=prompt,
            success=result.success,
        )
    )
    ctx.session.flush()

    return State.VALIDATING
