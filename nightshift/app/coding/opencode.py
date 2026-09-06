"""OpenCode CLI coding agent adapter."""

from __future__ import annotations

from pathlib import Path

from nightshift.app.coding.base import CodingRequest
from nightshift.app.coding.cli_agent_base import CLICodingAgent


class OpenCodeCodingAgent(CLICodingAgent):
    name = "opencode"
    cli_executable = "opencode"

    def _build_command(self, request: CodingRequest, prompt_file: Path) -> list[str]:
        return [
            self.cli_executable,
            "run",
            "--",
            prompt_file.read_text(encoding="utf-8"),
        ]
