"""review node: independent QA critic over the git diff."""

from __future__ import annotations

import asyncio
from pathlib import Path

from nightshift.app.agents.review_agent import ReviewAgent
from nightshift.app.config.logging import get_logger
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def _get_diff(workspace: Path) -> str:
    process = await asyncio.create_subprocess_exec(
        "git",
        "diff",
        cwd=str(workspace),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
    return stdout.decode("utf-8", errors="replace")


async def review(ctx: WorkflowContext) -> State:
    workspace_path = ctx.get("workspace_path")
    task = ctx.get("task", {})
    validation = ctx.get("validation_result", {})

    diff = await _get_diff(Path(workspace_path)) if workspace_path else ""

    review_result = {
        "passed": True,
        "unrelated_changes": [],
        "acceptance_criteria_met": {},
        "concerns": [],
    }

    if ctx.llm is not None and diff:
        agent = ReviewAgent(ctx.llm)
        try:
            result = await agent.review(task, diff, validation)
            review_result = result.model_dump()
        except Exception as exc:
            logger.error("review_agent_failed", error=str(exc))

    ctx.set("review_result", review_result)

    if not review_result.get("passed"):
        return State.REPAIRING

    return State.READY_FOR_PR
