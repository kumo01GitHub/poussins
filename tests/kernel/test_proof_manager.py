import pytest

from poussins.ast import EConst, EMetaVar
from poussins.errors import KernelStateError, KernelValueError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_manager import ProofManager
from poussins.kernel.proof_state import ProofState


def test_manager_initial_state_and_unclosed_status(default_env) -> None:
    manager = ProofManager(EConst("True", ()), default_env)

    assert not manager.is_closed
    assert manager.current_state.current_goal is not None
    assert manager.root_metavar_id is not None


def test_manager_current_proof_term_none_before_closure(default_env) -> None:
    manager = ProofManager(EConst("True", ()), default_env)

    assert manager.current_proof_term is None


def test_manager_close_goal_builds_proof_term(default_env) -> None:
    manager = ProofManager(EConst("True", ()), default_env)

    manager.close_goal(EConst("True.intro", ()))

    assert manager.is_closed
    assert manager.current_proof_term == EConst("True.intro", ())


def test_manager_undo_reverts_latest_step(default_env) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    manager.close_goal(EConst("True.intro", ()))

    manager.undo()

    assert not manager.is_closed
    assert manager.current_proof_term is None


def test_manager_refine_then_close_subgoal(default_env) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    current_goal = manager.current_state.current_goal
    subgoal = Goal(statement=EConst("True", ()), context=current_goal.context)

    manager.refine_goal(EMetaVar(subgoal.id), subgoals=[subgoal])
    assert not manager.is_closed

    manager.close_goal(EConst("True.intro", ()))

    assert manager.is_closed
    assert manager.current_proof_term == EConst("True.intro", ())


def test_manager_close_goal_without_active_goal_raises_kernel_state_error(default_env) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    manager.session.update_state(ProofState(goals=(), metavars={}))

    with pytest.raises(KernelStateError):
        manager.close_goal(EConst("True.intro", ()))


def test_manager_refine_goal_with_untracked_metavar_raises_kernel_value_error(default_env) -> None:
    manager = ProofManager(EConst("True", ()), default_env)

    with pytest.raises(KernelValueError):
        manager.refine_goal(EMetaVar("ghost"), subgoals=[])
