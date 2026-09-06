"""finalize node: mark execution completed."""

from __future__ import annotations

from nightshift.app.config.logging import get_logger
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def finalize(ctx: WorkflowContext) -> State:
    ctx.execution.active_coding = False
    ctx.session.flush()
    logger.info("execution_completed", execution_id=str(ctx.execution_id))
    return State.COMPLETED
