"""Tests for the structured output parser."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from nightshift.integrations.llm.parser import extract_json, parse_structured


class Sample(BaseModel):
    ready: bool
    missing_requirements: list[str]


def test_extract_plain_json() -> None:
    text = '{"ready": true, "missing_requirements": []}'
    assert extract_json(text) == text


def test_extract_fenced_json() -> None:
    text = 'Here is the result:\n```json\n{"ready": false, "missing_requirements": ["a"]}\n```'
    assert '"ready": false' in extract_json(text)


def test_parse_valid() -> None:
    result = parse_structured('{"ready": true, "missing_requirements": []}', Sample)
    assert result.ready is True
    assert result.missing_requirements == []


def test_parse_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse_structured("not json at all", Sample)
