"""LLM provider abstraction.

Night Shift must remain model-independent. The orchestration layer depends
on this interface, not on a concrete provider implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Model-independent LLM interface."""

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Return a plain-text completion for the given message list."""

    @abstractmethod
    async def structured_completion(
        self,
        prompt: str,
        schema: type[T],
        system: str | None = None,
    ) -> T:
        """Return a validated structured output (Pydantic model)."""
