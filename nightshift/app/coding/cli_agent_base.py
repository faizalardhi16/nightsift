"""Base class for CLI-based coding agents (subprocess invocation)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from nightshift.app.coding.base import CodingAgent, CodingRequest, CodingResult
from nightshift.app.config.logging import get_logger

logger = get_logger(__name__)


class CLICodingAgent(CodingAgent):
    """Runs a coding CLI with a prompt file inside a workspace."""

    name: str = "cli"
    cli_executable: str = ""

    def _build_command(self, request: CodingRequest, prompt_file: Path) -> list[str]:
        raise NotImplementedError

    async def execute(self, request: CodingRequest) -> CodingResult:
        started_at = datetime.now(UTC)
        workspace = Path(request.workspace_path)

        prompt_file = workspace / ".nightshift-prompt.md"
        prompt_file.write_text(request.prompt, encoding="utf-8")

        command = self._build_command(request, prompt_file)

        logger.info("coding_agent_start", agent=self.name, task_id=request.task_id)
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=request.timeout_seconds
            )
            exit_code = process.returncode
        except TimeoutError:
            logger.error(
                "coding_agent_timeout",
                agent=self.name,
                task_id=request.task_id,
                timeout=request.timeout_seconds,
            )
            return CodingResult(
                success=False,
                exit_code=None,
                stderr=f"Timed out after {request.timeout_seconds}s",
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )
        except Exception as exc:
            logger.error("coding_agent_failure", agent=self.name, error=str(exc))
            return CodingResult(
                success=False,
                exit_code=-1,
                stderr=str(exc),
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

        modified_files = await _list_modified_files(workspace)
        completed_at = datetime.now(UTC)
        logger.info(
            "coding_agent_finish",
            agent=self.name,
            task_id=request.task_id,
            exit_code=exit_code,
            modified_files=modified_files,
        )
        return CodingResult(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            modified_files=modified_files,
            started_at=started_at,
            completed_at=completed_at,
        )


async def _list_modified_files(workspace: Path) -> list[str]:
    """List modified files via git status --porcelain."""
    process = await asyncio.create_subprocess_exec(
        "git",
        "status",
        "--porcelain",
        cwd=str(workspace),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
    files = []
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        if line.strip():
            files.append(line[3:].strip())
    return files
