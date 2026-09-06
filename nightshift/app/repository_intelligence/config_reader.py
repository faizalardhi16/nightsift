"""Repository configuration reader (.nightshift.yml).

Repositories may provide a ``.nightshift.yml`` that overrides platform
defaults (PRD section 23).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "workflow": {
        "readiness_threshold": 90,
        "max_repair_attempts": 3,
    },
    "git": {
        "branch_prefix": "nightshift",
    },
    "coding": {
        "default_agent": "codex",
    },
    "security": {
        "forbidden_paths": [".env", "secrets/"],
    },
}


def load_repo_config(repo_path: Path) -> dict[str, Any]:
    """Load and merge .nightshift.yml with defaults."""
    config: dict[str, Any] = _deep_merge({}, DEFAULT_CONFIG)
    config_file = repo_path / ".nightshift.yml"
    if config_file.exists():
        try:
            data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
            config = _deep_merge(config, data)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid .nightshift.yml: {exc}") from exc
    return config


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
