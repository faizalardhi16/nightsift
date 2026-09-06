"""External task provider abstraction (PRD section 64)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class ExternalTask(BaseModel):
    id: str
    title: str
    description: str = ""
    project_code: str | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: int = 0
    status: str = ""
    metadata: dict = Field(default_factory=dict)


class TaskProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def get_candidates(self) -> list[ExternalTask]:
        """Return tasks available for processing."""

    @abstractmethod
    async def get_task(self, task_id: str) -> ExternalTask:
        """Return a single task by id."""

    @abstractmethod
    async def update_status(self, task_id: str, status: str) -> None:
        """Update the external task status."""
