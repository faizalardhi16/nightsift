"""Tests for ACE task payload normalization."""

from __future__ import annotations

import pytest

from nightshift.app.config.settings import Settings
from nightshift.integrations.task_provider.ace_mcp import AceMcpTaskProvider


@pytest.mark.parametrize("description", [None, 123, [], {}])
def test_map_task_normalizes_non_string_description(description: object) -> None:
    provider = AceMcpTaskProvider(Settings(_env_file=None))

    task = provider._map_task(
        {
            "id": "ace-id",
            "ref": "ACE-123",
            "title": "Task with optional description",
            "description": description,
        }
    )

    assert task.description == ""


def test_map_task_preserves_string_description() -> None:
    provider = AceMcpTaskProvider(Settings(_env_file=None))

    task = provider._map_task(
        {
            "id": "ace-id",
            "ref": "ACE-123",
            "title": "Task",
            "description": "Keep this description",
        }
    )

    assert task.description == "Keep this description"
