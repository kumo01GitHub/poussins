from types import SimpleNamespace

import pytest

from poussins.ast import EConst, ELam
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.kernel.proof_manager import ProofManager
from poussins.tactics.apply import apply


@pytest.fixture
def standard_env() -> Environment:
    return Environment.standard()


def test_apply_closes_goal_with_direct_constructor(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    apply(manager, EConst("True.intro", ()))

    assert manager.is_closed
    assert manager.current_proof_term == EConst("True.intro", ())


def test_apply_raises_when_no_goals_remain(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)
    apply(manager, EConst("True.intro", ()))

    with pytest.raises(TacticError):
        apply(manager, EConst("True.intro", ()))


def test_apply_raises_when_current_goal_is_missing(standard_env: Environment) -> None:
    class DummyManager:
        def __init__(self) -> None:
            self.is_closed = False
            self.current_state = SimpleNamespace(
                current_goal=None,
                metavars={},
            )

        def close_goal(self, _):
            raise RuntimeError("boom")

        def refine_goal(self, assignment, subgoals):
            raise RuntimeError("boom")

    manager = DummyManager()
    manager.current_state.current_goal = None

    with pytest.raises(TacticError):
        apply(manager, EConst("True.intro", ()))


def test_apply_enters_product_subgoal_path(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    with pytest.raises(TacticError):
        apply(manager, ELam("x", EConst("True", ()), EConst("True", ())))


def test_apply_wraps_kernel_failure(standard_env: Environment) -> None:
    class DummyManager:
        def __init__(self) -> None:
            self.is_closed = False
            self.current_state = SimpleNamespace(
                current_goal=SimpleNamespace(
                    statement=EConst("True", ()),
                    context={name: decl.type for name, decl in standard_env.items()},
                ),
                metavars={},
            )
            self.engine = SimpleNamespace(definitions={})

        def close_goal(self, assignment):
            raise RuntimeError("boom")

        def refine_goal(self, assignment, subgoals):
            raise RuntimeError("boom")

    manager = DummyManager()

    with pytest.raises(TacticError):
        apply(manager, EConst("True.intro", ()))
