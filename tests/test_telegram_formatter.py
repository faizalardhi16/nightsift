"""Tests for Telegram task clarification formatting."""

from __future__ import annotations

from nightshift.app.workflow.nodes.request_clarification import _default_questions
from nightshift.integrations.telegram.formatter import format_clarification


class _ContextStub:
    def __init__(self, state: dict) -> None:
        self._state = state

    def get(self, key: str, default=None):
        return self._state.get(key, default)


def test_clarification_uses_title_and_excludes_task_identifier() -> None:
    text = format_clarification(
        title="Export invoice to XLSX",
        score=55,
        questions=[
            {
                "question": "Apa tujuan utama task ini?",
                "reason": "Objective belum jelas.",
                "example": "Export invoice berdasarkan filter tanggal.",
                "options": [],
            }
        ],
    )

    assert "Export invoice to XLSX" in text
    assert "Task yang sedang diproses" in text
    assert "Apa tujuan utama task ini?" in text
    assert "Contoh jawaban: Export invoice berdasarkan filter tanggal." in text
    assert "Format jawaban:" in text
    assert "76f6eda8-8710-43a1-bbc2-e29142eef647" not in text


def test_clarification_has_safe_title_fallback() -> None:
    text = format_clarification(title="", score=20, questions=[])

    assert "Task tanpa judul" in text


def test_default_questions_explain_missing_requirements() -> None:
    questions = _default_questions(
        _ContextStub(
            {
                "readiness_analysis": {
                    "criteria": [
                        {
                            "key": "acceptance_criteria",
                            "satisfied": False,
                            "reason": "Belum ada kondisi selesai.",
                        }
                    ]
                }
            }
        )
    )

    assert questions[0]["question"] == (
        "Kriteria apa yang menentukan task ini sudah selesai dan benar?"
    )
    assert questions[0]["reason"] == "Belum ada kondisi selesai."
    assert questions[0]["example"]
