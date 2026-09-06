"""Codex CLI coding agent adapter."""

from __future__ import annotations

from pathlib import Path

from nightshift.app.coding.base import CodingRequest
from nightshift.app.coding.cli_agent_base import CLICodingAgent


class CodexCodingAgent(CLICodingAgent):
    name = "codex"
    cli_executable = "codex"

    def _build_command(self, request: CodingRequest, prompt_file: Path) -> list[str]:
        return [
            self.cli_executable,
            "--worktree",
            request.workspace_path,
            "--prompt-file",
            str(prompt_file),
        ]
