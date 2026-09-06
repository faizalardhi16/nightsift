"""Structured clarification questions produced for human-in-the-loop work."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClarificationQuestion(BaseModel):
    """One question that resolves an implementation-relevant ambiguity."""

    question: str = Field(min_length=1)
    reason: str = ""
    example: str = ""
    options: list[str] = Field(default_factory=list)


class ClarificationQuestions(BaseModel):
    """The bounded set of questions sent for the selected task."""

    questions: list[ClarificationQuestion] = Field(default_factory=list, max_length=5)
