"""Night Shift worker: polls for tasks and executes the workflow.

Enforces single active coding task via database advisory lock semantics
(one worker process in V1). When ``ace_mcp_enabled`` is set, the worker keeps
a long-lived Ace MCP session and syncs TODO tasks into the local queue before
claiming.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from nightshift.app.config.logging import configure_logging, get_logger
from nightshift.app.config.settings import get_settings
from nightshift.app.domains.task_scope import is_development_task
from nightshift.app.persistence.database import SessionLocal
from nightshift.app.persistence.models import Repository, TaskExecution
from nightshift.app.persistence.repositories.task_execution_repo import (
    TaskExecutionRepository,
)
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.runner import run_workflow
from nightshift.app.workflow.state import ACE_SYNC_BLOCKING_STATES, State
from nightshift.integrations.llm.azure_deepseek import AzureDeepseekProvider
from nightshift.integrations.task_provider.ace_mcp import AceMcpTaskProvider
from nightshift.integrations.task_provider.base import ExternalTask

logger = get_logger(__name__)

POLL_INTERVAL_SECONDS = 5
ACE_SYNC_INTERVAL_SECONDS = 300


def _resolve_repository(session, execution: TaskExecution) -> dict | None:
    if execution.repository_id is None:
        return None
    repo = session.get(Repository, execution.repository_id)
    if repo is None:
        return None
    return {
        "id": str(repo.id),
        "name": repo.name,
        "url": repo.url,
        "provider": repo.provider,
        "default_branch": repo.default_branch,
        "language": repo.language,
        "framework": repo.framework,
        "local_path": repo.local_path,
    }


async def _sync_ace_tasks(session, provider: AceMcpTaskProvider) -> int:
    """Pull only the first new TODO task from ACE into the local queue.

    Returns the number of tasks newly enqueued.
    """
    candidates = await provider.get_candidates()
    repo = TaskExecutionRepository(session)
    created = 0
    selected_task_ids: list[str] = []
    eligible_candidates = 0
    for task in candidates:
        if not is_development_task(task):
            logger.info(
                "ace_task_skipped_non_development",
                task_id=task.id,
                title=task.title,
            )
            continue
        eligible_candidates += 1
        existing = (
            session.query(TaskExecution)
            .filter(TaskExecution.external_task_id == task.id)
            .first()
        )
        if existing is None:
            repo.create(
                external_task_id=task.id,
                title=task.title,
                description=task.description,
                priority=task.priority,
            )
            created += 1
            selected_task_ids.append(task.id)
    if created:
        session.commit()
    logger.info(
        "ace_sync_complete",
        candidates=len(candidates),
        eligible_candidates=eligible_candidates,
        created=created,
        selected_task_ids=selected_task_ids,
    )
    return created


async def _sync_ace_if_idle(provider: AceMcpTaskProvider) -> None:
    """Sync ACE TODO tasks only when no local workflow is in progress."""
    with SessionLocal() as session:
        active_state = session.execute(
            select(TaskExecution.state)
            .where(TaskExecution.state.in_(ACE_SYNC_BLOCKING_STATES))
            .limit(1)
        ).scalar_one_or_none()
        if active_state is not None:
            logger.info(
                "ace_sync_skipped_active_task",
                active_state=active_state,
                interval_seconds=ACE_SYNC_INTERVAL_SECONDS,
            )
            return

        queued_task = session.execute(
            select(TaskExecution.id)
            .where(TaskExecution.state == State.QUEUED.value)
            .limit(1)
        ).scalar_one_or_none()
        if queued_task is not None:
            logger.info(
                "ace_sync_skipped_pending_task",
                interval_seconds=ACE_SYNC_INTERVAL_SECONDS,
            )
            return

        await _sync_ace_tasks(session, provider)


async def _run_ace_scheduler(provider: AceMcpTaskProvider) -> None:
    """Poll ACE immediately and then every five minutes while the worker runs."""
    logger.info(
        "ace_scheduler_started",
        interval_seconds=ACE_SYNC_INTERVAL_SECONDS,
    )
    while True:
        try:
            await _sync_ace_if_idle(provider)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - scheduler must keep running
            logger.exception("ace_scheduler_error", error=str(exc))
        await asyncio.sleep(ACE_SYNC_INTERVAL_SECONDS)


async def _process_one(provider: AceMcpTaskProvider | None) -> bool:
    """Process one eligible task. Returns True if a task was processed."""
    settings = get_settings()
    llm = AzureDeepseekProvider(settings) if settings.llm_configured else None

    with SessionLocal() as session:
        repo = TaskExecutionRepository(session)

        execution = repo.claim_next()
        if execution is None:
            if repo.has_blocking_execution():
                logger.info(
                    "task_claim_skipped_active_workflow",
                    interval_seconds=POLL_INTERVAL_SECONDS,
                )
            session.commit()
            return False

        if not is_development_task(
            ExternalTask(
                id=execution.external_task_id,
                title=execution.title or "",
                description=execution.description or "",
            )
        ):
            execution.state = State.FAILED.value
            execution.failure_reason = "Skipped: non-development task"
            execution.active_coding = False
            repo.log_event(
                execution.id,
                "NON_DEVELOPMENT_SKIPPED",
                State.CLAIMED.value,
                State.FAILED.value,
            )
            session.commit()
            logger.info(
                "task_skipped_non_development",
                execution_id=str(execution.id),
                external_task_id=execution.external_task_id,
                title=execution.title,
            )
            return True

        logger.info(
            "task_claimed",
            execution_id=str(execution.id),
            external_task_id=execution.external_task_id,
        )

        ctx = WorkflowContext(
            execution=execution,
            session=session,
            settings=settings,
            llm=llm,
            repo=repo,
            task_provider=provider,
        )
        ctx.set("repository", _resolve_repository(session, execution))

        try:
            await run_workflow(ctx)
        except Exception as exc:
            logger.exception(
                "workflow_exception",
                execution_id=str(execution.id),
                error=str(exc),
            )
            execution.state = State.FAILED.value
            execution.failure_reason = str(exc)
            execution.active_coding = False
        finally:
            session.commit()

        logger.info(
            "task_finished",
            execution_id=str(execution.id),
            final_state=execution.state,
        )
        return True


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("worker_started")

    provider: AceMcpTaskProvider | None = None
    ace_scheduler_task: asyncio.Task | None = None
    if settings.ace_mcp_enabled:
        provider = AceMcpTaskProvider(settings)
        try:
            await provider.connect()
            ace_scheduler_task = asyncio.create_task(_run_ace_scheduler(provider))
        except Exception as exc:
            logger.exception("ace_mcp_connect_failed", error=str(exc))
            provider = None
            logger.info("ace_scheduler_disabled", reason="ace_mcp_connect_failed")
    else:
        logger.info("ace_scheduler_disabled", reason="ACE_MCP_ENABLED=false")

    try:
        while True:
            try:
                processed = await _process_one(provider)
                if not processed:
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
            except Exception as exc:
                logger.exception("worker_loop_error", error=str(exc))
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
    finally:
        if ace_scheduler_task is not None:
            ace_scheduler_task.cancel()
            await asyncio.gather(ace_scheduler_task, return_exceptions=True)
        if provider is not None:
            await provider.close()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
