"""Tests for the state machine transitions."""

from __future__ import annotations

from nightshift.app.workflow.state import (
    ACE_SYNC_BLOCKING_STATES,
    State,
    is_ace_sync_blocked,
)
from nightshift.app.workflow.transitions import allowed_transitions, is_valid_transition


def test_valid_transition() -> None:
    assert is_valid_transition(State.QUEUED.value, State.CLAIMED.value)
    assert is_valid_transition(
        State.CONTEXT_BUILDING.value,
        State.NEED_CLARIFICATION.value,
    )
    assert is_valid_transition(State.REQUIREMENT_ANALYSIS.value, State.NEED_CLARIFICATION.value)
    assert is_valid_transition(State.VALIDATING.value, State.REPAIRING.value)
    assert is_valid_transition(State.NEED_CLARIFICATION.value, State.QUEUED.value)


def test_invalid_transition() -> None:
    assert not is_valid_transition(State.QUEUED.value, State.CODING.value)
    assert not is_valid_transition(State.COMPLETED.value, State.QUEUED.value)


def test_unknown_state() -> None:
    assert not is_valid_transition("NOPE", State.CLAIMED.value)
    assert allowed_transitions("NOPE") == set()


def test_ace_sync_is_blocked_for_active_workflow_states() -> None:
    assert is_ace_sync_blocked(State.CODING.value)
    assert is_ace_sync_blocked(State.WAITING_USER.value)
    assert State.QUEUED.value not in ACE_SYNC_BLOCKING_STATES


def test_ace_sync_is_allowed_for_terminal_states() -> None:
    assert not is_ace_sync_blocked(State.COMPLETED.value)
    assert not is_ace_sync_blocked(State.FAILED.value)
    assert not is_ace_sync_blocked(State.BLOCKED.value)


def test_terminal_has_no_transitions() -> None:
    assert allowed_transitions(State.COMPLETED.value) == set()
    assert allowed_transitions(State.BLOCKED.value) == set()
