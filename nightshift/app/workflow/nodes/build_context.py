"""build_context node: assemble a normalized TaskContext.

For Milestone 1-2 this builds context from the execution's task fields and,
when a repository is present, from repository intelligence.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from nightshift.app.config.logging import get_logger
from nightshift.app.config.project_directories import resolve_project_directory
from nightshift.app.persistence.models import ClarificationSession
from nightshift.app.repository_intelligence.context_builder import build_task_context
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def build_context(ctx: WorkflowContext) -> State:
    execution = ctx.execution
    task = {
        "id": execution.external_task_id,
        "title": execution.title or "Task tanpa judul",
        "description": execution.description or "",
        "acceptance_criteria": [],
    }

    # Enrich with full Ace detail when a task provider is available.
    if ctx.task_provider is not None:
        try:
            detail = await ctx.task_provider.get_task(execution.external_task_id)
            task["title"] = detail.title or task["title"]
            task["description"] = detail.description or task["description"]
            task["project_code"] = detail.project_code
            task["acceptance_criteria"] = detail.acceptance_criteria
        except Exception as exc:
            logger.warning("ace_task_detail_failed", error=str(exc))

    _apply_latest_clarification_answer(ctx, task)
    ctx.set("task", task)

    repository = ctx.get("repository")
    project_directory = resolve_project_directory(task.get("project_code"))
    if project_directory is not None:
        repository = {
            **(repository or {}),
            "name": task["project_code"],
            "url": str(project_directory),
            "provider": "local",
            "default_branch": (repository or {}).get("default_branch", "main"),
            "local_path": str(project_directory),
            "project_code": task["project_code"],
        }
        ctx.set("repository", repository)
        logger.info(
            "project_directory_resolved",
            project_code=task["project_code"],
            directory=str(project_directory),
        )

    if repository and repository.get("local_path"):
        repo_path = Path(repository["local_path"])
        if repo_path.exists():
            ctx.set(
                "context",
                build_task_context(task, repo_path, repository),
            )

    ctx.set("context", ctx.get("context") or {"task": task, "repository": repository or {}})

    # The first pass is always human clarification. Requirement readiness is
    # evaluated only after the user answers, so every selected ACE task is
    # visible in Telegram before any implementation decision is made.
    if ctx.get("clarification") is None:
        ctx.set("readiness_score", 0)
        ctx.set("readiness_analysis", {})
        logger.info(
            "clarification_first_pass",
            execution_id=str(ctx.execution_id),
        )
        return State.NEED_CLARIFICATION

    return State.REQUIREMENT_ANALYSIS


def _apply_latest_clarification_answer(ctx: WorkflowContext, task: dict) -> None:
    clarification = (
        ctx.session.execute(
            select(ClarificationSession)
            .where(
                ClarificationSession.task_execution_id == ctx.execution_id,
                ClarificationSession.status == "ANSWERED",
            )
            .order_by(
                ClarificationSession.answered_at.desc(),
                ClarificationSession.updated_at.desc(),
            )
            .limit(1)
        )
        .scalars()
        .first()
    )
    if clarification is None:
        return

    payload = {
        "raw_answer": clarification.raw_answer or "",
        "parsed_answer": clarification.parsed_answer or {},
    }
    task["clarification"] = payload
    ctx.set("clarification", payload)
