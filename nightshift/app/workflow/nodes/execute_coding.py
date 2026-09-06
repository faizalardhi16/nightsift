"""execute_coding node: invoke the coding agent."""

from __future__ import annotations

from nightshift.app.coding.base import CodingRequest
from nightshift.app.coding.registry import get_agent
from nightshift.app.config.logging import get_logger
from nightshift.app.persistence.models import AgentExecution
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def execute_coding(ctx: WorkflowContext) -> State:
    repository = ctx.get("repository", {})
    workspace_path = ctx.get("workspace_path")
    prompt = ctx.get("compiled_prompt", "")

    if not workspace_path:
        ctx.set("error", {"type": "WORKFLOW_INTERNAL_FAILURE", "message": "No workspace prepared"})
        return State.FAILED

    agent_name = (
        (ctx.get("context", {}).get("repo_config", {}).get("coding", {}) or {}).get(
            "default_agent"
        )
        or ctx.settings.default_coding_agent
    )

    request = CodingRequest(
        task_id=ctx.execution.external_task_id,
        repository_path=repository.get("local_path", ""),
        workspace_path=workspace_path,
        prompt=prompt,
        timeout_seconds=ctx.settings.coding_timeout_seconds,
    )

    try:
        agent = get_agent(agent_name)
    except ValueError:
        ctx.set("error", {"type": "CODING_AGENT_FAILURE", "message": f"Unknown agent {agent_name}"})
        return State.FAILED

    result = await agent.execute(request)

    record = AgentExecution(
        task_execution_id=ctx.execution_id,
        agent_type=agent_name,
        prompt=prompt,
        response=result.stdout[:100_000],
        success=result.success,
        started_at=result.started_at,
        completed_at=result.completed_at,
    )
    ctx.session.add(record)
    ctx.session.flush()

    ctx.set("coding_result", result.model_dump())
    if not result.success:
        logger.warning("coding_agent_returned_failure", agent=agent_name)
        ctx.set(
            "error",
            {
                "type": "CODING_AGENT_FAILURE",
                "message": result.stderr or "Coding agent failed",
            },
        )
        return State.FAILED

    return State.VALIDATING
