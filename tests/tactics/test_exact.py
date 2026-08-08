from types import SimpleNamespace

import pytest

from poussins.ast import EConst, EMetaVar, EVar
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_manager import ProofManager
from poussins.tactics.exact import assumption, exact


@pytest.fixture
def standard_env() -> Environment:
    return Environment.standard()


def test_exact_closes_goal(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    exact(manager, EConst("True.intro", ()))

    assert manager.is_closed
    assert manager.current_proof_term == EConst("True.intro", ())


def test_assumption_closes_goal_with_matching_hypothesis(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EConst("True", ())})

    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])
    assumption(manager)

    assert manager.is_closed
    assert manager.current_proof_term == EVar("h")


def test_assumption_raises_when_no_matching_hypothesis(standard_env: Environment) -> None:
    manager = ProofManager(EConst("False", ()), standard_env)

    with pytest.raises(TacticError):
        assumption(manager)


def test_exact_raises_when_no_active_goal() -> None:
    class DummyManager:
        def __init__(self) -> None:
            self.is_closed = False
            self.current_state = SimpleNamespace(current_goal=None, metavars={})

        def close_goal(self, assignment):
            raise RuntimeError("boom")

    manager = DummyManager()

    with pytest.raises(RuntimeError):
        exact(manager, EConst("True.intro", ()))


def test_assumption_raises_when_current_goal_is_missing() -> None:
    manager = SimpleNamespace(is_closed=False, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        assumption(manager)


def test_exact_and_assumption_reject_closed_manager() -> None:
    manager = SimpleNamespace(is_closed=True, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        exact(manager, EConst("True.intro", ()))

    with pytest.raises(TacticError):
        assumption(manager)
