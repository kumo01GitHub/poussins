from types import SimpleNamespace

import pytest

from poussins.ast import EApp, EConst, EMetaVar, ELam, ESort, EVar, UnivLevelZero
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_manager import ProofManager
from poussins.kernel.proof_state import ProofState
from poussins.tactics.change import change


@pytest.fixture
def standard_env() -> Environment:
    return Environment.standard()


def _beta_false():
    prop = ESort(UnivLevelZero())
    return EApp(ELam("P", prop, EVar("P")), EConst("False", ()))


def test_change_goal_replaces_current_target(standard_env: Environment) -> None:
    manager = ProofManager(EConst("False", ()), standard_env)

    change(manager, _beta_false())

    current_goal = manager.current_state.current_goal
    assert current_goal is not None
    assert current_goal.statement == _beta_false()


def test_change_hypothesis_replaces_local_type(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)
    current_goal = manager.current_state.current_goal
    subgoal = Goal(statement=EConst("True", ()), context=current_goal.context | {"hFalse": EConst("False", ())})
    manager.refine_goal(EMetaVar(subgoal.id), subgoals=[subgoal])

    change(manager, _beta_false(), "hFalse")

    updated_goal = manager.current_state.current_goal
    assert updated_goal is not None
    assert updated_goal.context["hFalse"] == _beta_false()


def test_change_rejects_closed_manager() -> None:
    manager = SimpleNamespace(is_closed=True)

    with pytest.raises(TacticError):
        change(manager, EConst("True", ()))


def test_change_requires_active_goal(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)
    manager.session.update_state(ProofState(goals=(), metavars={}))

    with pytest.raises(TacticError):
        change(manager, EConst("True", ()))


def test_change_wraps_kernel_errors_as_tactic_error(standard_env: Environment) -> None:
    manager = ProofManager(EConst("False", ()), standard_env)

    with pytest.raises(TacticError, match="definitionally equal"):
        change(manager, EConst("True", ()))