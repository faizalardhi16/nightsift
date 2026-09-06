"""Workflow graph: explicit state machine mapping states to handlers.

This is an explicit, deterministic state machine (PRD section 4.1 allows an
equivalent explicit workflow implementation instead of LangGraph).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.nodes import (
    analyze_impact,
    assess_readiness,
    build_context,
    compile_prompt,
    create_plan,
    create_pr,
    execute_coding,
    finalize,
    grab_task,
    install_baseline,
    prepare_workspace,
    repair,
    request_clarification,
    review,
    validate,
)
from nightshift.app.workflow.state import State

NodeFn = Callable[[WorkflowContext], Awaitable[State]]

GRAPH: dict[State, NodeFn] = {
    State.CLAIMED: grab_task.grab_task,
    State.CONTEXT_BUILDING: build_context.build_context,
    State.REQUIREMENT_ANALYSIS: assess_readiness.assess_readiness,
    State.NEED_CLARIFICATION: request_clarification.request_clarification,
    State.READY_TO_PLAN: analyze_impact.analyze_impact,
    State.IMPACT_ANALYSIS: create_plan.create_plan,
    State.PLANNING: compile_prompt.compile_prompt,
    State.READY_TO_CODE: prepare_workspace.prepare_workspace,
    State.WORKSPACE_PREPARATION: install_baseline.install_baseline,
    State.CODING: execute_coding.execute_coding,
    State.VALIDATING: validate.validate,
    State.REPAIRING: repair.repair,
    State.REVIEWING: review.review,
    State.READY_FOR_PR: create_pr.create_pr,
    State.PR_CREATED: finalize.finalize,
}


def get_node(state: State) -> NodeFn | None:
    return GRAPH.get(state)
