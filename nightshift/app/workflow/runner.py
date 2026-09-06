"""Workflow runner: executes the state machine loop for one execution."""

from __future__ import annotations

from nightshift.app.config.logging import get_logger
from nightshift.app.persistence.models import TaskExecution
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.graph import get_node
from nightshift.app.workflow.state import TERMINAL_STATES, State

logger = get_logger(__name__)

MAX_STEPS = 50


async def run_workflow(ctx: WorkflowContext) -> State:
    """Run the state machine until a terminal or waiting state.

    The caller is responsible for committing the session.
    """
    current = State(ctx.execution.state)

    for _ in range(MAX_STEPS):
        if current in TERMINAL_STATES:
            return current
        if current == State.WAITING_USER:
            return current

        node = get_node(current)
        if node is None:
            logger.error(
                "no_node_for_state",
                state=current.value,
                execution_id=str(ctx.execution_id),
            )
            ctx.repo.transition(ctx.execution, State.FAILED)
            return State.FAILED

        next_state = await node(ctx)

        if next_state in TERMINAL_STATES:
            _finalize_terminal(ctx, next_state)
            return next_state

        if next_state == State.WAITING_USER:
            ctx.repo.transition(ctx.execution, State.WAITING_USER)
            return State.WAITING_USER

        if next_state == State.QUEUED:
            ctx.repo.transition(ctx.execution, State.QUEUED)
            return State.QUEUED

        ctx.repo.transition(ctx.execution, next_state)
        current = next_state

    logger.error(
        "workflow_step_limit_exceeded",
        execution_id=str(ctx.execution_id),
        max_steps=MAX_STEPS,
    )
    ctx.repo.transition(ctx.execution, State.FAILED)
    return State.FAILED


def _finalize_terminal(ctx: WorkflowContext, state: State) -> None:
    execution: TaskExecution = ctx.execution
    execution.active_coding = False
    error = ctx.get("error")
    if state in (State.BLOCKED, State.FAILED) and error:
        execution.failure_reason = str(error)
    ctx.repo.transition(execution, state)
