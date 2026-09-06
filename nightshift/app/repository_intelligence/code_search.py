"""Grep-based code search (simple, deterministic).

V1 avoids complex RAG / vector search (PRD section 95). This provides a
lightweight way to locate files likely related to a task.
"""

from __future__ import annotations

import re
from pathlib import Path

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next"}

_SOURCE_EXTENSIONS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".py",
    ".go",
    ".java",
    ".kt",
    ".dart",
    ".cs",
    ".rb",
    ".php",
}


def tokenize(text: str) -> list[str]:
    """Split text into searchable tokens (camelCase-aware)."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]+", text)
    expanded: list[str] = []
    for w in words:
        expanded.append(w.lower())
        parts = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", w)
        for p in parts:
            if len(p) > 2:
                expanded.append(p.lower())
    return list(dict.fromkeys(expanded))


def search_code(repo_path: Path, query: str, limit: int = 20) -> list[dict]:
    """Return files whose path/content matches the query tokens."""
    tokens = tokenize(query)
    if not tokens:
        return []

    matches: list[dict] = []
    pattern = re.compile("|".join(re.escape(t) for t in tokens), re.IGNORECASE)

    for file in repo_path.rglob("*"):
        if not file.is_file():
            continue
        if any(part in _SKIP_DIRS for part in file.parts):
            continue
        if file.suffix not in _SOURCE_EXTENSIONS:
            continue

        rel = file.relative_to(repo_path).as_posix()
        score = 0
        if pattern.search(rel):
            score += 3
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        content_hits = len(pattern.findall(content[:200_000]))
        if content_hits:
            score += min(content_hits, 10)

        if score > 0:
            matches.append({"path": rel, "score": score})

        if len(matches) >= limit:
            break

    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches[:limit]
