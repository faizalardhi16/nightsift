"""Azure OpenAI (Deepseek-V4-Flash) LLM provider.

Migrated from the reference ``cli_agent`` implementation. Extends the plain
chat client with ``structured_completion`` used by Night Shift's internal
reasoning agents.
"""

from __future__ import annotations

import time
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from nightshift.app.config.logging import get_logger
from nightshift.app.config.settings import Settings
from nightshift.integrations.llm.base import LLMProvider
from nightshift.integrations.llm.parser import parse_structured

T = TypeVar("T", bound=BaseModel)

OPENAI_ROUTE = "/openai/v1/"

logger = get_logger(__name__)


def build_base_url(endpoint: str) -> str:
    """Normalize the Azure endpoint into an OpenAI-compatible base URL."""
    normalized = endpoint.rstrip("/")
    if normalized.endswith("/openai/v1"):
        return f"{normalized}/"
    if normalized.endswith("/openai/v1/"):
        return normalized
    return f"{normalized}{OPENAI_ROUTE}"


class AzureDeepseekProvider(LLMProvider):
    """Deepseek-V4-Flash served through Azure OpenAI."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=build_base_url(settings.azure_openai_endpoint),
        )

    @property
    def model(self) -> str:
        return self._settings.azure_openai_model

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        started = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Model returned an empty response.")
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "llm_chat_success",
                model=self.model,
                duration_ms=duration_ms,
            )
            return content
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.error(
                "llm_chat_failure",
                model=self.model,
                duration_ms=duration_ms,
                error=str(exc),
            )
            raise RuntimeError(f"Request to Azure OpenAI failed: {exc}") from exc

    async def structured_completion(
        self,
        prompt: str,
        schema: type[T],
        system: str | None = None,
        max_retries: int = 2,
    ) -> T:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            text = await self.chat(messages)
            try:
                return parse_structured(text, schema)
            except ValueError as exc:
                last_error = exc
                logger.warning(
                    "llm_structured_parse_retry",
                    model=self.model,
                    attempt=attempt + 1,
                    error=str(exc),
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was not valid. Return ONLY a "
                            f"valid JSON object matching this schema. Error: {exc}"
                        ),
                    }
                )

        raise RuntimeError(
            f"Structured completion failed after {max_retries + 1} attempts: {last_error}"
        )
