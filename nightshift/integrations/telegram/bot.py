"""Telegram bot client (send messages)."""

from __future__ import annotations

import httpx

from nightshift.app.config.logging import get_logger

logger = get_logger(__name__)


class TelegramClient:
    def __init__(self, bot_token: str, default_chat_id: str | None = None) -> None:
        self._token = bot_token
        self._default_chat_id = default_chat_id
        self._base_url = f"https://api.telegram.org/bot{bot_token}"

    @property
    def configured(self) -> bool:
        return bool(self._token)

    async def send_message(self, text: str, chat_id: str | None = None) -> int | None:
        """Send a message and return the message_id."""
        if not self.configured:
            logger.warning("telegram_not_configured")
            return None

        target = chat_id or self._default_chat_id
        if not target:
            logger.warning("telegram_no_chat_id")
            return None

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self._base_url}/sendMessage",
                json={"chat_id": target, "text": text},
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                logger.error("telegram_send_failed", error=data)
                return None
            return data["result"]["message_id"]
