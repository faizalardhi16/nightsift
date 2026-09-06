"""Telegram message formatting (PRD sections 28, 78)."""

from __future__ import annotations


def format_clarification(title: str, score: int, questions: list[dict]) -> str:
    """Format clarification for the single task currently being processed."""
    display_title = title.strip() or "Task tanpa judul"
    lines = [
        "Night Shift - Clarification Required",
        "",
        f"Task yang sedang diproses\n{display_title}",
        "",
        f"Readiness\n{score} / 100",
        "",
        "Task ini belum cukup jelas untuk dikerjakan tanpa asumsi.",
        "Mohon lengkapi pertanyaan berikut:",
        "",
    ]
    for index, question in enumerate(questions, start=1):
        lines.append(f"{index}. {question['question']}")
        if question.get("reason"):
            lines.append(f"   Kenapa: {question['reason']}")
        for letter, option in enumerate(question.get("options", [])):
            lines.append(f"   {chr(65 + letter)}. {option}")
        if question.get("example"):
            lines.append(f"   Contoh jawaban: {question['example']}")
        lines.append("")

    lines.extend(
        [
            "Format jawaban:",
            "1. <jawaban untuk pertanyaan nomor 1>",
            "2. <jawaban untuk pertanyaan nomor 2>",
            "...",
            "",
            "Contoh: 1. Tujuannya menambahkan endpoint export invoice; "
            "2. File terdampak adalah modul invoice.",
        ]
    )
    return "\n".join(lines)


def format_completed(
    title: str,
    pr_url: str,
    branch: str,
    repair_attempts: int,
) -> str:
    """Format a success notification (PRD section 78)."""
    display_title = title.strip() or "Task tanpa judul"
    return (
        "Night Shift completed\n\n"
        f"Task\n{display_title}\n\n"
        "Status\nPR Ready for Review\n\n"
        f"Pull Request\n{pr_url}\n\n"
        f"Repair Attempts\n{repair_attempts}\n\n"
        f"Branch\n{branch}"
    )


def format_blocked(title: str, reason: str, branch: str | None) -> str:
    """Format a blocked notification (PRD section 78)."""
    display_title = title.strip() or "Task tanpa judul"
    return (
        "Night Shift blocked\n\n"
        f"Task\n{display_title}\n\n"
        f"Reason\n{reason}\n\n"
        f"Branch preserved:\n{branch or 'n/a'}\n\n"
        "Human review required."
    )
