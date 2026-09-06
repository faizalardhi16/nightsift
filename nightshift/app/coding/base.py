"""Coding agent abstraction (PRD sections 39-41).

The core workflow depends on this interface, never on a concrete CLI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel


class CodingRequest(BaseModel):
    task_id: str
    repository_path: str
    workspace_path: str
    prompt: str
    timeout_seconds: int = 3600
    allowed_paths: list[str] = []


class CodingResult(BaseModel):
    success: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    modified_files: list[str] = []
    started_at: datetime | None = None
    completed_at: datetime | None = None


class CodingAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def execute(self, request: CodingRequest) -> CodingResult:
        """Execute the coding agent against the workspace."""
