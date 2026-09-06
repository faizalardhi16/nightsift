"""Tests for the local Telegram long-polling consumer."""

from __future__ import annotations

import pytest

from nightshift.app.config.settings import Settings
from nightshift.integrations.telegram.poller import TelegramPoller, create_poller


@pytest.mark.asyncio
async def test_process_updates_filters_non_allowed_chats() -> None:
    poller = TelegramPoller(bot_token="token", chat_id="111")
    applied: list[tuple[str, str]] = []

    def _record(chat_id: str, text: str) -> None:
        applied.append((chat_id, text))

    poller._apply_answer = _record  # type: ignore[method-assign]

    await poller._process_updates(
        [
            {"update_id": 1, "message": {"chat": {"id": 999}, "text": "ignored"}},
            {"update_id": 2, "message": {"chat": {"id": 111}, "text": "accepted"}},
            {"update_id": 3, "message": {"chat": {"id": 111}}},  # no text
        ]
    )

    assert applied == [("111", "accepted")]
    assert poller._offset == 4  # all updates acked, including ignored ones


@pytest.mark.asyncio
async def test_process_updates_skips_edited_and_non_text_updates() -> None:
    poller = TelegramPoller(bot_token="token", chat_id="111")
    applied: list[str] = []

    def _record(chat_id: str, text: str) -> None:
        applied.append(text)

    poller._apply_answer = _record  # type: ignore[method-assign]

    await poller._process_updates(
        [
            {"update_id": 1, "message": {"chat": {"id": 111}, "text": "halo"}},
            {"update_id": 2, "edited_message": {"chat": {"id": 111}, "text": "edit"}},
            {"update_id": 3, "message": {"chat": {"id": 111}, "photo": []}},
        ]
    )

    assert applied == ["halo"]


def test_create_poller_requires_token_and_chat_id() -> None:
    assert (
        create_poller(Settings(telegram_bot_token="", telegram_chat_id="111"))
        is None
    )
    assert (
        create_poller(Settings(telegram_bot_token="tok", telegram_chat_id=""))
        is None
    )

    poller = create_poller(
        Settings(telegram_bot_token="tok", telegram_chat_id="111")
    )
    assert poller is not None
    assert poller._chat_id == "111"
