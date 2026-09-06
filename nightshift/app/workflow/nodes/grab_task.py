"""grab_task node: task is already claimed before entering the graph.

Transitions the execution into context building.
"""

from __future__ import annotations

from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State


async def grab_task(ctx: WorkflowContext) -> State:
    # Claiming is performed atomically by the worker before graph execution.
    ctx.repo.log_event(ctx.execution_id, "TASK_GRABBED", None, None)
    return State.CONTEXT_BUILDING
