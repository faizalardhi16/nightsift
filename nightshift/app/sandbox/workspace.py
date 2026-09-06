"""Workspace lifecycle via Git worktrees (PRD sections 42-43)."""

from __future__ import annotations

import shutil
from pathlib import Path

from nightshift.app.config.logging import get_logger
from nightshift.app.sandbox.command_runner import CommandRunner

logger = get_logger(__name__)


class WorkspaceManager:
    def __init__(self, runner: CommandRunner, workspace_root: Path) -> None:
        self._runner = runner
        self._workspace_root = workspace_root

    @property
    def root(self) -> Path:
        return self._workspace_root

    async def create_worktree(
        self,
        repo_path: Path,
        task_id: str,
        branch_name: str,
        base_ref: str = "origin/main",
    ) -> Path:
        """Create a dedicated worktree + branch for the task."""
        workspace = self._workspace_root / task_id
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)

        result = await self._runner.execute(
            [
                "git",
                "worktree",
                "add",
                str(workspace),
                "-b",
                branch_name,
                base_ref,
            ],
            cwd=repo_path,
            timeout=120,
        )
        if not result.success:
            raise RuntimeError(
                f"git worktree add failed: {result.stderr or result.stdout}"
            )
        logger.info("worktree_created", task_id=task_id, path=str(workspace))
        return workspace

    async def remove_worktree(self, repo_path: Path, task_id: str) -> None:
        workspace = self._workspace_root / task_id
        if not workspace.exists():
            return
        await self._runner.execute(
            ["git", "worktree", "remove", "--force", str(workspace)],
            cwd=repo_path,
            timeout=60,
        )
        shutil.rmtree(workspace, ignore_errors=True)
        logger.info("worktree_removed", task_id=task_id)
