"""create_plan node: produce an implementation plan."""

from __future__ import annotations

from nightshift.app.agents.planning_agent import PlanningAgent
from nightshift.app.config.logging import get_logger
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def create_plan(ctx: WorkflowContext) -> State:
    task = ctx.get("task", {})
    impact = ctx.get("impact_analysis", {})
    context = ctx.get("context", {})

    plan = {"steps": [], "test_strategy": "", "blockers": []}

    if ctx.llm is not None:
        agent = PlanningAgent(ctx.llm)
        try:
            result = await agent.plan(task, impact, context)
            plan = result.model_dump()
        except Exception as exc:
            logger.error("planning_agent_failed", error=str(exc))

    if plan.get("blockers"):
        ctx.set("error", {"type": "REQUIREMENT_FAILURE", "message": str(plan["blockers"])})
        return State.FAILED

    ctx.set("implementation_plan", plan)
    return State.PLANNING
