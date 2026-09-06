"""GitHub provider."""

from __future__ import annotations

from github import Github

from nightshift.app.config.logging import get_logger
from nightshift.integrations.git_provider.base import (
    GitProvider,
    PullRequestRequest,
    PullRequestResult,
)

logger = get_logger(__name__)


class GitHubProvider(GitProvider):
    name = "github"

    def __init__(self, token: str) -> None:
        self._client = Github(token)

    async def create_pull_request(self, request: PullRequestRequest) -> PullRequestResult:
        repo = self._client.get_repo(request.repository)
        pr = repo.create_pull(
            title=request.title,
            body=request.body,
            head=request.head_branch,
            base=request.base_branch,
        )
        logger.info("github_pr_created", number=pr.number, url=pr.html_url)
        return PullRequestResult(
            provider=self.name,
            number=pr.number,
            external_id=str(pr.id),
            url=pr.html_url,
        )

    async def add_comment(self, pull_request_id: str, comment: str) -> None:
        pr = self._client.get_repo(pull_request_id)
        # pull_request_id is expected to be "owner/repo#number"
        if "#" in pull_request_id:
            repo_slug, number = pull_request_id.rsplit("#", 1)
            pr = self._client.get_repo(repo_slug).get_pull(int(number))
            pr.create_issue_comment(comment)
