"""Validation pipeline (PRD sections 47-48).

Runs repository-configured build/lint/test commands and records results.
"""

from __future__ import annotations

from pathlib import Path

from nightshift.app.config.logging import get_logger
from nightshift.app.sandbox.command_runner import CommandRunner

logger = get_logger(__name__)


class ValidationRunner:
    def __init__(self, runner: CommandRunner) -> None:
        self._runner = runner

    async def run(
        self,
        workspace: Path,
        validation_config: dict,
    ) -> dict:
        """Run configured validation stages and return a result payload."""
        results: dict[str, dict] = {}
        passed = True

        for stage in ("build", "lint", "unit_test", "integration_test"):
            command = validation_config.get(stage, {}).get("command")
            if not command:
                continue
            stage_result = await self._run_stage(workspace, stage, command)
            results[stage] = stage_result
            if stage_result["status"] != "PASS":
                passed = False

        return {"stages": results, "passed": passed}

    async def _run_stage(self, workspace: Path, stage: str, command: str) -> dict:
        parts = command.split()
        result = await self._runner.execute(
            parts,
            cwd=workspace,
            timeout=900,
            allow_shell=True,
        )
        return {
            "status": "PASS" if result.success else "FAIL",
            "command": command,
            "exit_code": result.exit_code,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }


async def run_baseline(workspace: Path, install_command: str | None) -> dict:
    """Run installation + baseline validation before coding (PRD section 44)."""
    runner = CommandRunner()
    result = {"install": None, "baseline_failure": False, "detail": ""}

    if install_command:
        install_result = await runner.execute(
            install_command.split(),
            cwd=workspace,
            timeout=900,
            allow_shell=True,
        )
        result["install"] = {
            "command": install_command,
            "exit_code": install_result.exit_code,
        }
        if not install_result.success:
            result["baseline_failure"] = True
            result["detail"] = install_result.stderr or install_result.stdout
            return result

    return result
