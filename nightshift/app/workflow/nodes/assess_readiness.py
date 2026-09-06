"""assess_readiness node: compute evidence-based readiness score.

If an LLM provider is available, use the requirement agent; otherwise fall
back to a heuristic. The application owns the final score.
"""

from __future__ import annotations

from nightshift.app.agents.requirement_agent import RequirementAgent
from nightshift.app.config.logging import get_logger
from nightshift.app.domains.readiness import (
    ReadinessAnalysis,
    compute_readiness_score,
)
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State
from nightshift.integrations.task_provider.ace_mcp import update_ace_status

logger = get_logger(__name__)


async def assess_readiness(ctx: WorkflowContext) -> State:
    task = ctx.get("task", {})
    context = ctx.get("context", {})

    score = 0
    analysis: ReadinessAnalysis | None = None

    if ctx.llm is not None:
        agent = RequirementAgent(ctx.llm)
        try:
            analysis = await agent.analyze(task, context)
            score = compute_readiness_score(analysis)
        except Exception as exc:
            logger.error("readiness_agent_failed", error=str(exc))

    if analysis is None:
        # Heuristic fallback: give partial credit based on available fields.
        score = _heuristic_score(task)

    ctx.set("readiness_score", score)
    ctx.set("readiness_analysis", analysis.model_dump() if analysis else {})
    ctx.repo.set_readiness(ctx.execution, score)

    threshold = ctx.settings.readiness_threshold
    logger.info("readiness_scored", execution_id=str(ctx.execution_id), score=score)

    if score >= threshold:
        # Confidence is high enough to start work: move Ace task to IN_PROGRESS.
        await update_ace_status(ctx.task_provider, ctx.execution.external_task_id, "IN_PROGRESS")
        return State.READY_TO_PLAN
    return State.NEED_CLARIFICATION


def _heuristic_score(task: dict) -> int:
    score = 0
    if task.get("title"):
        score += 15  # objective partially clear
    if task.get("description"):
        score += 20  # some acceptance info present
    if task.get("acceptance_criteria"):
        score += 20
    return min(score, 100)
