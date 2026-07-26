"""Tests for the run state machine."""
import pytest

from agent_api.state_machine.run_fsm import RunEvent, RunStateMachine
from aai_core.domain import RunStatus
from aai_core.errors import AAIError


class TestRunStateMachine:
    def test_initial_pending(self):
        fsm = RunStateMachine(RunStatus.PENDING)
        assert fsm.status == RunStatus.PENDING
        assert not fsm.is_terminal

    def test_pending_to_running(self):
        fsm = RunStateMachine(RunStatus.PENDING)
        new = fsm.apply(RunEvent.START)
        assert new == RunStatus.RUNNING

    def test_running_to_done(self):
        fsm = RunStateMachine(RunStatus.RUNNING)
        assert fsm.apply(RunEvent.COMPLETE) == RunStatus.DONE

    def test_running_to_failed(self):
        fsm = RunStateMachine(RunStatus.RUNNING)
        assert fsm.apply(RunEvent.FAIL) == RunStatus.FAILED

    def test_running_to_paused(self):
        fsm = RunStateMachine(RunStatus.RUNNING)
        assert fsm.apply(RunEvent.PAUSE) == RunStatus.PAUSED

    def test_paused_to_running(self):
        fsm = RunStateMachine(RunStatus.PAUSED)
        assert fsm.apply(RunEvent.RESUME) == RunStatus.RUNNING

    def test_cancel_from_pending(self):
        fsm = RunStateMachine(RunStatus.PENDING)
        assert fsm.apply(RunEvent.CANCEL) == RunStatus.CANCELLED

    def test_cancel_from_running(self):
        fsm = RunStateMachine(RunStatus.RUNNING)
        assert fsm.apply(RunEvent.CANCEL) == RunStatus.CANCELLED

    def test_done_is_terminal(self):
        fsm = RunStateMachine(RunStatus.DONE)
        assert fsm.is_terminal

    def test_failed_is_terminal(self):
        fsm = RunStateMachine(RunStatus.FAILED)
        assert fsm.is_terminal

    def test_cancelled_is_terminal(self):
        fsm = RunStateMachine(RunStatus.CANCELLED)
        assert fsm.is_terminal

    def test_invalid_transition_raises(self):
        fsm = RunStateMachine(RunStatus.DONE)
        with pytest.raises(AAIError) as exc:
            fsm.apply(RunEvent.START)
        assert exc.value.http_status == 409

    def test_cannot_complete_from_pending(self):
        fsm = RunStateMachine(RunStatus.PENDING)
        assert not fsm.can(RunEvent.COMPLETE)

    def test_can_cancel_from_running(self):
        fsm = RunStateMachine(RunStatus.RUNNING)
        assert fsm.can(RunEvent.CANCEL)

    def test_full_happy_path(self):
        fsm = RunStateMachine(RunStatus.PENDING)
        fsm.apply(RunEvent.START)
        fsm.apply(RunEvent.COMPLETE)
        assert fsm.status == RunStatus.DONE
        assert fsm.is_terminal

    def test_hitl_flow(self):
        fsm = RunStateMachine(RunStatus.RUNNING)
        fsm.apply(RunEvent.PAUSE)
        assert fsm.status == RunStatus.PAUSED
        fsm.apply(RunEvent.RESUME)
        assert fsm.status == RunStatus.RUNNING
        fsm.apply(RunEvent.COMPLETE)
        assert fsm.status == RunStatus.DONE
