"""Workflow execution context.

Carries everything a node needs: the execution row, repository, services,
and typed accessors for reading/writing workflow state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from nightshift.app.config.settings import Settings
from nightshift.app.persistence.models import TaskExecution
from nightshift.app.persistence.repositories.task_execution_repo import (
    TaskExecutionRepository,
)
from nightshift.integrations.llm.base import LLMProvider
from nightshift.integrations.task_provider.base import TaskProvider


@dataclass
class WorkflowContext:
    """Shared context for a single task execution run."""

    execution: TaskExecution
    session: Session
    settings: Settings
    llm: LLMProvider | None
    repo: TaskExecutionRepository
    task_provider: TaskProvider | None = None
    state: dict[str, Any] = field(default_factory=dict)

    @property
    def execution_id(self):
        return self.execution.id

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value
