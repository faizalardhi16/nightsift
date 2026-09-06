"""Claude Code CLI coding agent adapter."""

from __future__ import annotations

from pathlib import Path

from nightshift.app.coding.base import CodingRequest
from nightshift.app.coding.cli_agent_base import CLICodingAgent


class ClaudeCodeCodingAgent(CLICodingAgent):
    name = "claude_code"
    cli_executable = "claude"

    def _build_command(self, request: CodingRequest, prompt_file: Path) -> list[str]:
        return [
            self.cli_executable,
            "-p",  # print (non-interactive)
            "--output-format",
            "text",
            "--allowedTools",
            "Bash,Edit,Write,Read",
            "--",
            prompt_file.read_text(encoding="utf-8"),
        ]
