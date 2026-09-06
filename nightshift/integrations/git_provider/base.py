"""Git provider abstraction (PRD section 65)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class PullRequestRequest(BaseModel):
    repository: str
    title: str
    body: str
    head_branch: str
    base_branch: str = "main"


class PullRequestResult(BaseModel):
    provider: str
    number: int | None = None
    external_id: str | None = None
    url: str | None = None


class GitProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def create_pull_request(self, request: PullRequestRequest) -> PullRequestResult:
        ...

    @abstractmethod
    async def add_comment(self, pull_request_id: str, comment: str) -> None:
        ...
