"""Task-related request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class TaskCreateRequest(BaseModel):
    external_task_id: str
    title: str | None = None
    description: str | None = None
    priority: int = 0
    repository_id: uuid.UUID | None = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    external_task_id: str
    state: str
    title: str | None = None
    readiness_score: int | None = None
    priority: int = 0
    branch_name: str | None = None
    repair_attempt: int = 0
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    from_state: str | None = None
    to_state: str | None = None
    payload: dict | None = None
    created_at: datetime | None = None
