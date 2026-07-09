"""State machine orchestration (constitution §3 / §14).

This module is a *thin* facade over :mod:`app.student_recognition.state_model`.
It contains NO business algorithm — it only validates and applies transitions,
guaranteeing that every status change complies with the single source of truth.
"""

from typing import Any

from app.student_recognition.state_model import (
    IllegalTransitionError,
    State,
    apply_transition,
    can_transition,
)

__all__ = [
    "State",
    "IllegalTransitionError",
    "can_transition",
    "apply_transition",
    "transition",
    "assert_can_transition",
]


def transition(job: Any, to: State) -> None:
    """Apply a single-step transition to ``job`` (delegates to state_model)."""
    apply_transition(job, to)


def assert_can_transition(frm: State, to: State) -> None:
    """Raise ``IllegalTransitionError`` if ``frm -> to`` is not allowed."""
    if not can_transition(frm, to):
        raise IllegalTransitionError(frm, to)
