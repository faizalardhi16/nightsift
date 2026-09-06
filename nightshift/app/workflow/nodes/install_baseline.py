"""install_baseline node: install dependencies + baseline validation.

Runs before coding so pre-existing failures are attributed correctly
(PRD section 44).
"""

from __future__ import annotations

from pathlib import Path

from nightshift.app.config.logging import get_logger
from nightshift.app.domains.validation import run_baseline
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def install_baseline(ctx: WorkflowContext) -> State:
    workspace_path = ctx.get("workspace_path")
    if not workspace_path:
        ctx.set("error", {"type": "WORKFLOW_INTERNAL_FAILURE", "message": "No workspace"})
        return State.FAILED

    repo_config = ctx.get("context", {}).get("repo_config", {})
    install_command = (repo_config.get("installation", {}) or {}).get("command")

    baseline = await run_baseline(Path(workspace_path), install_command)
    ctx.set("baseline", baseline)

    if baseline.get("baseline_failure"):
        logger.warning("baseline_failure", detail=baseline.get("detail", "")[:500])
        ctx.set(
            "error",
            {"type": "DEPENDENCY_INSTALL_FAILURE", "message": baseline.get("detail", "")[:2000]},
        )
        return State.FAILED

    return State.CODING
