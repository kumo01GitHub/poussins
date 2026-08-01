import pytest

from poussins.ast import EConst
from poussins.errors import KernelStateError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_session import ProofSession
from poussins.kernel.proof_state import MetaVar, ProofState


def _state_with_single_goal(statement_name: str) -> ProofState:
    goal = Goal(statement=EConst(statement_name, ()), context={})
    return ProofState(goals=(goal,), metavars={goal.id: MetaVar(statement=goal.statement)})


def test_session_initial_state_and_history() -> None:
    initial_state = _state_with_single_goal("True")
    session = ProofSession(initial_state)

    assert session.current_state == initial_state
    assert session.history == (initial_state,)
    assert not session.is_closed


def test_session_update_state_appends_history() -> None:
    initial_state = _state_with_single_goal("True")
    next_state = ProofState(goals=(), metavars=initial_state.metavars)
    session = ProofSession(initial_state)

    session.update_state(next_state)

    assert session.current_state == next_state
    assert session.history == (initial_state, next_state)
    assert session.is_closed


def test_session_undo_reverts_to_previous_state() -> None:
    initial_state = _state_with_single_goal("True")
    next_state = ProofState(goals=(), metavars=initial_state.metavars)
    session = ProofSession(initial_state)
    session.update_state(next_state)

    session.undo()

    assert session.current_state == initial_state
    assert session.history == (initial_state,)


def test_session_undo_beyond_initial_raises() -> None:
    session = ProofSession(_state_with_single_goal("True"))

    with pytest.raises(KernelStateError):
        session.undo()
