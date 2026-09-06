"""FastAPI application entrypoint for Night Shift."""

from __future__ import annotations

from contextlib import asynccontextmanager

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
    yield
    logger.info("nightshift_shutdown")
    await engine.dispose()


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
