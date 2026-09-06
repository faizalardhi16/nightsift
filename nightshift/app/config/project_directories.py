"""Project-code to local source-directory mapping.

The mapping is intentionally kept in one place because ACE supplies a project
code while the workflow needs the local Git repository path.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_DIRECTORY_MAP: dict[str, Path] = {
    "EXON": Path(r"D:\fromdoc\EXON_V2"),
    "SPBI": Path(r"D:\fromdoc\spbi\dev-spbi"),
}


def resolve_project_directory(project_code: str | None) -> Path | None:
    """Return the configured directory for an ACE project code."""
    if not project_code:
        return None
    return PROJECT_DIRECTORY_MAP.get(project_code.strip().upper())
