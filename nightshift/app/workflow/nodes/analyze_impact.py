"""analyze_impact node: identify affected modules/files."""

from __future__ import annotations

from nightshift.app.agents.impact_agent import ImpactAgent
from nightshift.app.config.logging import get_logger
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def analyze_impact(ctx: WorkflowContext) -> State:
    task = ctx.get("task", {})
    context = ctx.get("context", {})

    impact = {"affected_modules": [], "affected_files": [], "risks": []}

    if ctx.llm is not None:
        agent = ImpactAgent(ctx.llm)
        try:
            result = await agent.analyze(task, context)
            impact = result.model_dump()
        except Exception as exc:
            logger.error("impact_agent_failed", error=str(exc))

    ctx.set("impact_analysis", impact)
    return State.IMPACT_ANALYSIS
