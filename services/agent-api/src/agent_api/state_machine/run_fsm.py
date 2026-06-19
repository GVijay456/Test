"""Run state machine — enforces valid transitions.

Valid transitions:
  PENDING  → RUNNING
  RUNNING  → DONE | FAILED | PAUSED | CANCELLED
  PAUSED   → RUNNING | CANCELLED
  DONE     (terminal)
  FAILED   (terminal)
  CANCELLED (terminal)
"""
from __future__ import annotations

from enum import StrEnum

from aai_core.domain import RunStatus
from aai_core.errors import AAIError, ErrorCode

# Maps current status → set of valid next statuses
_VALID_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.PENDING:   {RunStatus.RUNNING, RunStatus.CANCELLED},
    RunStatus.RUNNING:   {RunStatus.DONE, RunStatus.FAILED, RunStatus.PAUSED, RunStatus.CANCELLED},
    RunStatus.PAUSED:    {RunStatus.RUNNING, RunStatus.CANCELLED},
    RunStatus.DONE:      set(),
    RunStatus.FAILED:    set(),
    RunStatus.CANCELLED: set(),
}


class RunEvent(StrEnum):
    START     = "start"
    COMPLETE  = "complete"
    FAIL      = "fail"
    PAUSE     = "pause"     # HITL waiting
    RESUME    = "resume"
    CANCEL    = "cancel"


_EVENT_TARGET: dict[RunEvent, RunStatus] = {
    RunEvent.START:    RunStatus.RUNNING,
    RunEvent.COMPLETE: RunStatus.DONE,
    RunEvent.FAIL:     RunStatus.FAILED,
    RunEvent.PAUSE:    RunStatus.PAUSED,
    RunEvent.RESUME:   RunStatus.RUNNING,
    RunEvent.CANCEL:   RunStatus.CANCELLED,
}


class RunStateMachine:
    """Pure state machine — no DB or I/O. Validates transitions only."""

    def __init__(self, current_status: RunStatus) -> None:
        self._status = current_status

    @property
    def status(self) -> RunStatus:
        return self._status

    @property
    def is_terminal(self) -> bool:
        return not _VALID_TRANSITIONS[self._status]

    def apply(self, event: RunEvent) -> RunStatus:
        """Apply event, return new status. Raises AAIError if invalid."""
        target = _EVENT_TARGET[event]
        allowed = _VALID_TRANSITIONS[self._status]

        if target not in allowed:
            raise AAIError(
                ErrorCode.RUN_NOT_FOUND,  # reuse — caller can remap
                f"Cannot apply {event!r} to run in status {self._status!r}. "
                f"Allowed transitions: {[s.value for s in allowed]}",
                http_status=409,
            )

        self._status = target
        return self._status

    def can(self, event: RunEvent) -> bool:
        return _EVENT_TARGET[event] in _VALID_TRANSITIONS[self._status]
