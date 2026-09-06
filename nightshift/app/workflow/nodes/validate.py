"""validate node: run the validation pipeline."""

from __future__ import annotations

from pathlib import Path

from nightshift.app.config.logging import get_logger
from nightshift.app.domains.validation import ValidationRunner
from nightshift.app.sandbox.command_runner import CommandRunner
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def validate(ctx: WorkflowContext) -> State:
    workspace_path = ctx.get("workspace_path")
    if not workspace_path:
        ctx.set("error", {"type": "WORKFLOW_INTERNAL_FAILURE", "message": "No workspace"})
        return State.FAILED

    repo_config = ctx.get("context", {}).get("repo_config", {})
    validation_config = repo_config.get("validation", {})

    runner = CommandRunner(allowed_cwd=Path(workspace_path))
    validation_runner = ValidationRunner(runner)

    result = await validation_runner.run(Path(workspace_path), validation_config)
    ctx.set("validation_result", result)

    if not result["passed"]:
        if ctx.execution.repair_attempt >= ctx.settings.max_repair_attempts:
            return State.BLOCKED
        return State.REPAIRING

    return State.REVIEWING
