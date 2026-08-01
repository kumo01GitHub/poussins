import pytest

from poussins.ast import EConst, EMetaVar, ELam, EPi, ESort, EVar, UnivLevelZero
from poussins.errors import KernelStateError, KernelValueError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_engine import ProofEngine
from poussins.kernel.proof_state import ProofState


def test_create_initial_state_has_single_goal_and_metavar(default_env) -> None:
    engine = ProofEngine(default_env)
    statement = EConst("True", ())

    state = engine.create_initial_state(statement)

    assert len(state.goals) == 1
    assert state.current_goal is not None
    assert state.current_goal.statement == statement
    assert state.current_goal.id in state.metavars
    assert state.metavars[state.current_goal.id].statement == statement
    assert not state.metavars[state.current_goal.id].is_assigned


def test_close_goal_successfully_closes_true_goal(default_env) -> None:
    engine = ProofEngine(default_env)
    state = engine.create_initial_state(EConst("True", ()))

    next_state = engine.close_goal(state, EConst("True.intro", ()))

    assert next_state.goals == ()
    assert state.current_goal.id in next_state.metavars
    assert next_state.metavars[state.current_goal.id].is_assigned


def test_close_goal_without_active_goal_raises(default_env) -> None:
    engine = ProofEngine(default_env)
    state = ProofState(goals=(), metavars={})

    with pytest.raises(KernelStateError):
        engine.close_goal(state, EConst("True.intro", ()))


def test_refine_goal_rejects_untracked_metavars(default_env) -> None:
    engine = ProofEngine(default_env)
    state = engine.create_initial_state(EConst("True", ()))

    with pytest.raises(KernelValueError):
        engine.refine_goal(state, EMetaVar("ghost"), subgoals=[])


def test_refine_goal_rejects_subgoal_missing_in_assignment(default_env) -> None:
    engine = ProofEngine(default_env)
    state = engine.create_initial_state(EConst("True", ()))
    subgoal = Goal(statement=EConst("True", ()), context=state.current_goal.context)

    with pytest.raises(KernelValueError):
        engine.refine_goal(state, EConst("True.intro", ()), subgoals=[subgoal])


def test_refine_goal_rejects_already_registered_metavar(default_env) -> None:
    engine = ProofEngine(default_env)
    state = engine.create_initial_state(EConst("True", ()))
    current = state.current_goal

    with pytest.raises(KernelStateError):
        engine.refine_goal(state, EMetaVar(current.id), subgoals=[current])


def test_refine_goal_adds_explicit_subgoal(default_env) -> None:
    engine = ProofEngine(default_env)
    state = engine.create_initial_state(EConst("True", ()))
    new_subgoal = Goal(statement=EConst("True", ()), context=state.current_goal.context)

    next_state = engine.refine_goal(state, EMetaVar(new_subgoal.id), subgoals=[new_subgoal])

    assert next_state.current_goal == new_subgoal
    assert new_subgoal.id in next_state.metavars
    assert not next_state.metavars[new_subgoal.id].is_assigned
    assert next_state.metavars[state.current_goal.id].assignment == EMetaVar(new_subgoal.id)


def test_close_goal_accepts_alpha_equivalent_lambda_term(default_env) -> None:
    engine = ProofEngine(default_env)
    prop = ESort(UnivLevelZero())
    statement = EPi("x", prop, prop)
    state = engine.create_initial_state(statement)

    next_state = engine.close_goal(state, ELam("y", prop, EVar("y")))

    assert next_state.goals == ()
    assert next_state.metavars[state.current_goal.id].is_assigned
