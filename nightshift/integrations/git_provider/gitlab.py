"""GitLab provider (including self-hosted instances like git.dexagroup.com)."""

from __future__ import annotations

import gitlab

from nightshift.app.config.logging import get_logger
from nightshift.integrations.git_provider.base import (
    GitProvider,
    PullRequestRequest,
    PullRequestResult,
)

logger = get_logger(__name__)


class GitLabProvider(GitProvider):
    name = "gitlab"

    def __init__(self, url: str, token: str) -> None:
        self._client = gitlab.Gitlab(url=url, private_token=token)

    def _get_project(self, repository: str):
        return self._client.projects.get(repository)

    async def create_pull_request(self, request: PullRequestRequest) -> PullRequestResult:
        project = self._get_project(request.repository)
        mr = project.mergerequests.create(
            {
                "source_branch": request.head_branch,
                "target_branch": request.base_branch,
                "title": request.title,
                "description": request.body,
                "remove_source_branch": False,
            }
        )
        logger.info("gitlab_mr_created", iid=mr.iid, url=mr.web_url)
        return PullRequestResult(
            provider=self.name,
            number=mr.iid,
            external_id=str(mr.id),
            url=mr.web_url,
        )

    async def add_comment(self, pull_request_id: str, comment: str) -> None:
        # pull_request_id is expected to be "project_path#iid"
        if "#" not in pull_request_id:
            return
        project_path, iid = pull_request_id.rsplit("#", 1)
        project = self._get_project(project_path)
        mr = project.mergerequests.get(int(iid))
        mr.notes.create({"body": comment})
