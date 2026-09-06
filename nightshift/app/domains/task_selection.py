"""Selection rules for choosing the next task from the local queue."""

from __future__ import annotations

import re

# Title-only ranking keeps selection deterministic and does not spend an LLM
# call before the selected task reaches the human clarification step.
_EASY_TERMS = (
    "typo",
    "label",
    "text",
    "copy",
    "rename",
    "color",
    "spacing",
    "placeholder",
    "button",
    "tombol",
    "teks",
    "warna",
)

_COMPLEX_TERMS = (
    "migration",
    "migrate",
    "refactor",
    "integrat",
    "authentication",
    "authorization",
    "permission",
    "performance",
    "concurren",
    "workflow",
    "architecture",
    "database",
    "schema",
    "bulk",
    "import",
    "export",
)


def title_ease_score(title: str | None) -> int:
    """Return a deterministic ease score based only on the task title."""
    normalized = (title or "").strip().lower()
    if not normalized:
        return 0

    words = re.findall(r"[a-z0-9]+", normalized)
    score = 100 - max(0, len(words) - 6) * 4
    score += sum(12 for term in _EASY_TERMS if term in normalized)
    score -= sum(18 for term in _COMPLEX_TERMS if term in normalized)
    return max(score, 0)
