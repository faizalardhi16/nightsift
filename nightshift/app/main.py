"""FastAPI application entrypoint for Night Shift."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from nightshift.app.config.logging import configure_logging, get_logger
from nightshift.app.config.settings import ensure_directories, get_settings
from nightshift.app.persistence.database import engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    ensure_directories(settings)
    logger.info("nightshift_startup")

    # Local deployments behind NAT cannot receive Telegram webhooks; when
    # polling is enabled we consume replies via long-polling instead.
    poller_task: asyncio.Task | None = None
    if settings.telegram_polling_enabled:
        from nightshift.integrations.telegram.poller import create_poller

        poller = create_poller(settings)
        if poller is not None:
            poller_task = asyncio.create_task(poller.run())

    yield

    if poller_task is not None:
        poller_task.cancel()
        with suppress(asyncio.CancelledError):
            await poller_task
    logger.info("nightshift_shutdown")
    # dispose() is synchronous — awaiting it would raise at shutdown.
    engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Night Shift", version="0.1.0", lifespan=lifespan)
    _register_routes(app)
    return app


def _register_routes(app: FastAPI) -> None:
    from nightshift.app.api.routes import health, llm_probe, tasks, webhooks, workflow

    app.include_router(health.router)
    app.include_router(llm_probe.router)
    app.include_router(tasks.router)
    app.include_router(workflow.router)
    app.include_router(webhooks.router)


app = create_app()
