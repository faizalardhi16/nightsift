"""Tests for ACE project-code directory resolution."""

from __future__ import annotations

from pathlib import Path

from nightshift.app.config.project_directories import resolve_project_directory
from nightshift.app.config.settings import Settings
from nightshift.integrations.task_provider.ace_mcp import AceMcpTaskProvider


def test_project_code_resolves_case_insensitively() -> None:
    assert resolve_project_directory("exon") == Path(r"D:\fromdoc\EXON_V2")
    assert resolve_project_directory(" SPBI ") == Path(r"D:\fromdoc\spbi\dev-spbi")


def test_unknown_project_code_is_not_resolved() -> None:
    assert resolve_project_directory("UNKNOWN") is None
    assert resolve_project_directory(None) is None


def test_ace_task_reads_project_code() -> None:
    provider = AceMcpTaskProvider(Settings())

    task = provider._map_task(
        {
            "id": "ace-id",
            "ref": "EXON-001",
            "title": "Update EXON",
            "project": {"code": "exon"},
            "status": "TODO",
        }
    )

    assert task.project_code == "EXON"
