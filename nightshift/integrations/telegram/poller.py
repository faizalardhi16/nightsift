"""Local Telegram long-polling consumer.

Drop-in transport replacement for the webhook route when Night Shift runs on a
local computer behind NAT (no public HTTPS URL for Telegram to reach).

Reuses the same answer-resolution logic as the webhook
(``hitl.apply_telegram_answer``), so behaviour is identical regardless of which
transport delivered the reply.

Enable with ``TELEGRAM_POLLING_ENABLED=true``. Do NOT register the webhook
(``setWebhook``) while polling is active — both transports fight over updates.
"""

from __future__ import annotations

import asyncio

import httpx

from nightshift.app.config.logging import get_logger
from nightshift.app.config.settings import Settings
from nightshift.app.persistence.database import SessionLocal
from nightshift.integrations.telegram.hitl import apply_telegram_answer

logger = get_logger(__name__)

_RETRY_DELAY_SECONDS = 5.0
_POLL_TIMEOUT_SECONDS = 30
_REQUEST_TIMEOUT_SECONDS = 45


class TelegramPoller:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        poll_timeout: int = _POLL_TIMEOUT_SECONDS,
        request_timeout: int = _REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._chat_id = str(chat_id)
        self._poll_timeout = poll_timeout
        self._request_timeout = request_timeout
        self._offset = 0
        self._stopping = False

    def stop(self) -> None:
        """Signal the run loop to exit between iterations."""
        self._stopping = True

    async def run(self) -> None:
        logger.info("telegram_polling_started", chat_id=self._chat_id)
        while not self._stopping:
            try:
                async with httpx.AsyncClient(timeout=self._request_timeout) as client:
                    response = await client.get(
                        f"{self._base_url}/getUpdates",
                        params={"offset": self._offset, "timeout": self._poll_timeout},
                    )
                    response.raise_for_status()
                    payload = response.json()
                if payload.get("ok"):
                    await self._process_updates(payload.get("result", []))
                else:
                    logger.error("telegram_polling_api_error", error=payload)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("telegram_polling_error", error=str(exc))
                await asyncio.sleep(_RETRY_DELAY_SECONDS)
        logger.info("telegram_polling_stopped")

    async def _process_updates(self, updates: list[dict]) -> None:
        for update in updates:
            update_id = update.get("update_id")
            if update_id is not None:
                # Ack before processing so Telegram never redelivers it.
                self._offset = update_id + 1

            message = update.get("message") or {}
            text = message.get("text")
            chat_id = message.get("chat", {}).get("id")
            if not text or chat_id is None:
                continue
            if str(chat_id) != self._chat_id:
                logger.info("telegram_polling_ignored_chat", chat_id=chat_id)
                continue

            await asyncio.to_thread(self._apply_answer, str(chat_id), text)

    def _apply_answer(self, chat_id: str, text: str) -> None:
        with SessionLocal() as db:
            try:
                applied = apply_telegram_answer(db, chat_id, text)
                if not applied:
                    logger.info("telegram_polling_no_open_session")
            except Exception as exc:
                logger.error("telegram_polling_process_failed", error=str(exc))


def create_poller(settings: Settings) -> TelegramPoller | None:
    """Build the poller, or ``None`` when Telegram is not configured."""
    if not settings.telegram_bot_token:
        logger.error("telegram_polling_requires_token")
        return None
    if not settings.telegram_chat_id:
        logger.error("telegram_polling_requires_chat_id")
        return None
    return TelegramPoller(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    )
