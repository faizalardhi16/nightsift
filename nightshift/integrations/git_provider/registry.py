"""Git provider factory."""

from __future__ import annotations

from nightshift.app.config.settings import Settings
from nightshift.integrations.git_provider.base import GitProvider
from nightshift.integrations.git_provider.github import GitHubProvider
from nightshift.integrations.git_provider.gitlab import GitLabProvider


def get_git_provider(settings: Settings, provider: str) -> GitProvider:
    if provider == "github":
        if not settings.github_token:
            raise ValueError("GITHUB_TOKEN is not configured")
        return GitHubProvider(settings.github_token)
    if provider == "gitlab":
        if not settings.gitlab_token:
            raise ValueError("GITLAB_TOKEN is not configured")
        return GitLabProvider(settings.gitlab_url, settings.gitlab_token)
    raise ValueError(f"Unknown git provider: {provider}")
