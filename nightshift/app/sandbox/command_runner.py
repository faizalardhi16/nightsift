"""Command runner (PRD sections 45-46).

All command execution passes through this runner. It enforces forbidden-command
policies and timeouts. No unrestricted shell access.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from nightshift.app.config.logging import get_logger
from nightshift.app.sandbox.policies import CommandResult, is_forbidden

logger = get_logger(__name__)


class CommandPolicyViolation(Exception):
    pass


class CommandRunner:
    def __init__(self, allowed_cwd: Path | None = None) -> None:
        self._allowed_cwd = allowed_cwd

    async def execute(
        self,
        command: list[str],
        cwd: Path,
        timeout: int = 600,
        allow_shell: bool = False,
    ) -> CommandResult:
        joined = " ".join(command)
        forbidden = is_forbidden(joined)
        if forbidden:
            raise CommandPolicyViolation(
                f"Forbidden command pattern detected: {forbidden!r}"
            )

        if self._allowed_cwd is not None:
            resolved = cwd.resolve()
            if not str(resolved).startswith(str(self._allowed_cwd.resolve())):
                raise CommandPolicyViolation(
                    f"cwd {resolved} is outside allowed workspace {self._allowed_cwd}"
                )

        started = time.perf_counter()
        logger.info("command_start", command=joined, cwd=str(cwd))
        try:
            if allow_shell:
                process = await asyncio.create_subprocess_shell(
                    joined,
                    cwd=str(cwd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=str(cwd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except TimeoutError as exc:
            logger.error("command_timeout", command=joined, timeout=timeout)
            raise RuntimeError(f"Command timed out after {timeout}s: {joined}") from exc

        duration_ms = int((time.perf_counter() - started) * 1000)
        result = CommandResult(
            command=command,
            exit_code=process.returncode if process.returncode is not None else -1,
            stdout=(stdout or b"").decode("utf-8", errors="replace"),
            stderr=(stderr or b"").decode("utf-8", errors="replace"),
            duration_ms=duration_ms,
        )
        logger.info(
            "command_finish",
            command=joined,
            exit_code=result.exit_code,
            duration_ms=duration_ms,
        )
        return result
