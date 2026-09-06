"""prepare_workspace node: create a dedicated git worktree."""

from __future__ import annotations

from pathlib import Path

from nightshift.app.config.logging import get_logger
from nightshift.app.sandbox.command_runner import CommandRunner
from nightshift.app.sandbox.workspace import WorkspaceManager
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def prepare_workspace(ctx: WorkflowContext) -> State:
    repository = ctx.get("repository", {})
    local_path = repository.get("local_path")
    if not local_path:
        ctx.set("error", {"type": "REPOSITORY_FAILURE", "message": "Repository not configured"})
        return State.FAILED

    repo_path = Path(local_path)
    task_id = ctx.execution.external_task_id

    branch_prefix = (ctx.get("context", {}).get("repo_config", {}).get("git", {}) or {}).get(
        "branch_prefix", "nightshift"
    )
    branch_name = f"{branch_prefix}/{_slugify(task_id)}"

    runner = CommandRunner(allowed_cwd=Path(ctx.settings.workspace_root))
    manager = WorkspaceManager(runner, Path(ctx.settings.workspace_root))

    try:
        workspace = await manager.create_worktree(
            repo_path=repo_path,
            task_id=_slugify(task_id),
            branch_name=branch_name,
            base_ref=f"origin/{repository.get('default_branch', 'main')}",
        )
    except Exception as exc:
        logger.error("workspace_creation_failed", error=str(exc))
        ctx.set("error", {"type": "REPOSITORY_FAILURE", "message": str(exc)})
        return State.FAILED

    ctx.set("branch_name", branch_name)
    ctx.set("workspace_path", str(workspace))
    ctx.execution.branch_name = branch_name
    ctx.execution.workspace_path = str(workspace)
    ctx.execution.active_coding = True
    ctx.session.flush()

    return State.WORKSPACE_PREPARATION


def _slugify(value: str) -> str:
    import re

    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-") or "task"
