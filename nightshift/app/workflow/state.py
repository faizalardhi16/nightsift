"""Workflow state definitions.

Represents the complete workflow context (PRD section 15) and the internal
state machine states (PRD section 16).
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


class State(StrEnum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    CONTEXT_BUILDING = "CONTEXT_BUILDING"
    REQUIREMENT_ANALYSIS = "REQUIREMENT_ANALYSIS"
    NEED_CLARIFICATION = "NEED_CLARIFICATION"
    WAITING_USER = "WAITING_USER"
    READY_TO_PLAN = "READY_TO_PLAN"
    IMPACT_ANALYSIS = "IMPACT_ANALYSIS"
    PLANNING = "PLANNING"
    READY_TO_CODE = "READY_TO_CODE"
    WORKSPACE_PREPARATION = "WORKSPACE_PREPARATION"
    CODING = "CODING"
    VALIDATING = "VALIDATING"
    REPAIRING = "REPAIRING"
    REVIEWING = "REVIEWING"
    READY_FOR_PR = "READY_FOR_PR"
    PR_CREATING = "PR_CREATING"
    PR_CREATED = "PR_CREATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


TERMINAL_STATES = {State.COMPLETED, State.FAILED, State.BLOCKED}

# A task in any of these states owns the active workflow. New ACE intake is
# paused until that workflow reaches a terminal state.
ACE_SYNC_BLOCKING_STATES = frozenset(
    state.value
    for state in State
    if state not in TERMINAL_STATES and state is not State.QUEUED
)

ACTIVE_CODING_STATES = {
    State.WORKSPACE_PREPARATION,
    State.CODING,
    State.VALIDATING,
    State.REPAIRING,
    State.REVIEWING,
}


def is_ace_sync_blocked(state: str) -> bool:
    """Return whether a local workflow should pause ACE intake."""
    return state in ACE_SYNC_BLOCKING_STATES


class NightShiftState(TypedDict, total=False):
    execution_id: str
    task_id: str
    current_state: str
    task: dict
    repository: dict
    context: dict
    readiness_score: int
    readiness_analysis: dict
    clarification: dict | None
    impact_analysis: dict | None
    implementation_plan: dict | None
    compiled_prompt: str | None
    coding_result: dict | None
    validation_result: dict | None
    repair_attempt: int
    branch_name: str | None
    workspace_path: str | None
    pull_request: dict | None
    error: dict | None
