"""State transition validation.

Enforces that only valid transitions occur (PRD sections 16-17).
"""

from __future__ import annotations

from nightshift.app.workflow.state import State

_VALID_TRANSITIONS: dict[State, set[State]] = {
    State.QUEUED: {State.CLAIMED},
    State.CLAIMED: {State.CONTEXT_BUILDING, State.FAILED},
    State.CONTEXT_BUILDING: {
        State.REQUIREMENT_ANALYSIS,
        State.NEED_CLARIFICATION,
        State.FAILED,
    },
    State.REQUIREMENT_ANALYSIS: {
        State.NEED_CLARIFICATION,
        State.READY_TO_PLAN,
        State.FAILED,
    },
    State.NEED_CLARIFICATION: {State.WAITING_USER, State.QUEUED, State.FAILED},
    State.WAITING_USER: {State.REQUIREMENT_ANALYSIS, State.BLOCKED, State.FAILED},
    State.READY_TO_PLAN: {State.IMPACT_ANALYSIS, State.FAILED},
    State.IMPACT_ANALYSIS: {State.PLANNING, State.FAILED},
    State.PLANNING: {State.READY_TO_CODE, State.FAILED},
    State.READY_TO_CODE: {State.WORKSPACE_PREPARATION, State.FAILED},
    State.WORKSPACE_PREPARATION: {State.CODING, State.FAILED},
    State.CODING: {State.VALIDATING, State.FAILED},
    State.VALIDATING: {State.REPAIRING, State.REVIEWING, State.BLOCKED, State.FAILED},
    State.REPAIRING: {State.VALIDATING, State.BLOCKED, State.FAILED},
    State.REVIEWING: {State.READY_FOR_PR, State.REPAIRING, State.FAILED},
    State.READY_FOR_PR: {State.PR_CREATING, State.PR_CREATED, State.FAILED},
    State.PR_CREATING: {State.PR_CREATED, State.FAILED},
    State.PR_CREATED: {State.COMPLETED, State.FAILED},
    State.COMPLETED: set(),
    State.FAILED: set(),
    State.BLOCKED: set(),
}


def is_valid_transition(from_state: str, to_state: str) -> bool:
    try:
        f = State(from_state)
        t = State(to_state)
    except ValueError:
        return False
    return t in _VALID_TRANSITIONS.get(f, set())


def allowed_transitions(state: str) -> set[str]:
    try:
        f = State(state)
    except ValueError:
        return set()
    return {s.value for s in _VALID_TRANSITIONS.get(f, set())}
