"""Coding agent registry / factory."""

from __future__ import annotations

from nightshift.app.coding.base import CodingAgent
from nightshift.app.coding.claude_code import ClaudeCodeCodingAgent
from nightshift.app.coding.codex import CodexCodingAgent
from nightshift.app.coding.opencode import OpenCodeCodingAgent

AGENTS: dict[str, type[CodingAgent]] = {
    "codex": CodexCodingAgent,
    "claude_code": ClaudeCodeCodingAgent,
    "opencode": OpenCodeCodingAgent,
}


def get_agent(name: str) -> CodingAgent:
    try:
        return AGENTS[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown coding agent: {name}") from exc
