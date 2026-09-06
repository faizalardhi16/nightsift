"""Telegram webhook handler (PRD section 30).

Receives incoming messages, identifies the clarification session, parses the
answer, and triggers workflow resume.
"""

from __future__ import annotations

from nightshift.app.config.logging import get_logger

logger = get_logger(__name__)


def parse_answer(raw: str, question_count: int) -> list[str]:
    """Parse a multi-line answer like "1A\\n2B\\n10000" into a list."""
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    answers: list[str] = []
    for line in lines:
        if line and (line[0].isdigit()):
            answers.append(line)
        else:
            answers.append(line)
    return answers[:question_count]
