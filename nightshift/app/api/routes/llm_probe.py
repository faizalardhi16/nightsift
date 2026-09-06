"""LLM probe endpoint for verifying Azure Deepseek connectivity."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from nightshift.app.config.settings import get_settings
from nightshift.integrations.llm.azure_deepseek import AzureDeepseekProvider

router = APIRouter(prefix="/api/v1/test", tags=["test"])


class LLMProbeResponse(BaseModel):
    answer: str


@router.post("/llm", response_model=LLMProbeResponse)
async def probe_llm() -> LLMProbeResponse:
    settings = get_settings()
    provider = AzureDeepseekProvider(settings)
    answer = await provider.chat(
        [{"role": "user", "content": "Reply with exactly: NIGHT SHIFT OK"}]
    )
    return LLMProbeResponse(answer=answer)
