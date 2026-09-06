"""Configuration settings for Night Shift."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+psycopg://nightshift:nightshift@localhost:5432/nightshift"

    # Azure OpenAI
    azure_openai_endpoint: str = "https://iu-techpool-production.services.ai.azure.com"
    azure_openai_api_key: str = ""
    azure_openai_model: str = "deepseek-v4-flash"
    azure_openai_api_version: str = "2024-06-01"

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_chat_id: str = ""
    # true = jawaban user diproses via long-polling (mode lokal / tanpa webhook)
    telegram_polling_enabled: bool = False

    # Git providers
    gitlab_url: str = "https://git.dexagroup.com"
    gitlab_token: str = ""
    github_token: str = ""

    # Ace (MCP task provider)
    ace_mcp_enabled: bool = False
    ace_base_url: str = "https://apigw.dexagroup.com/ace"
    ace_api_key: str = ""
    ace_gateway_api_key: str = ""

    # Workflow
    max_active_coding_tasks: int = 1
    max_repair_attempts: int = 3
    readiness_threshold: int = 90
    workspace_root: str = "/workspaces"
    repository_root: str = "/repos"

    # Coding agents
    default_coding_agent: str = "codex"
    coding_timeout_seconds: int = 3600

    # Logging
    log_level: str = "INFO"

    @property
    def llm_configured(self) -> bool:
        return bool(self.azure_openai_api_key)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def ensure_directories(settings: Settings) -> None:
    """Create runtime directories if missing."""
    for raw in (settings.workspace_root, settings.repository_root):
        path = Path(raw)
        path.mkdir(parents=True, exist_ok=True)
