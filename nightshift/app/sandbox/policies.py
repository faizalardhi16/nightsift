"""Command result and policy definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CommandResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int = 0

    @property
    def success(self) -> bool:
        return self.exit_code == 0


FORBIDDEN_PATTERNS: list[str] = [
    "rm -rf /",
    "rm -fr /",
    "sudo ",
    "shutdown",
    "reboot",
    "mkfs",
    "git push --force",
    "git push -f",
    ":(){ :|:& };:",
    "> /dev/sda",
    "dd if=",
]


def is_forbidden(command: str) -> str | None:
    """Return the forbidden pattern that matched, or None."""
    lowered = command.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in lowered:
            return pattern
    return None
