"""Skill loader: load SKILL.md files from the skills directory."""

from __future__ import annotations

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[3] / "skills"


def list_skills() -> dict[str, Path]:
    """Return a map of skill name -> SKILL.md path."""
    if not SKILLS_DIR.exists():
        return {}
    return {
        skill_dir.name: skill_dir / "SKILL.md"
        for skill_dir in SKILLS_DIR.iterdir()
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists()
    }


def load_skill(name: str) -> str | None:
    """Load the SKILL.md content for a skill by name."""
    skills = list_skills()
    path = skills.get(name)
    if path is None:
        return None
    return path.read_text(encoding="utf-8", errors="ignore")
