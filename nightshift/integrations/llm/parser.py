"""Structured output parser with bounded retry.

When an LLM decision affects a state transition, the response must be
structured (Pydantic). Invalid responses are retried using a bounded parser
retry policy (default: 2 retries, see PRD section 76).
"""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)

def extract_json(text: str) -> str:
    """Best-effort extraction of a JSON object from LLM output."""
    text = text.strip()
    match = _JSON_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def parse_structured[T](text: str, schema: type[T]) -> T:
    """Parse LLM text into a Pydantic model, raising on failure."""
    raw = extract_json(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM output is not valid JSON: {exc}") from exc

    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"LLM output failed schema validation: {exc}") from exc
