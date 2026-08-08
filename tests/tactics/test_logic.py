from types import SimpleNamespace

import pytest

from poussins.ast import EConst
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.kernel.proof_manager import ProofManager
from poussins.tactics.logic import exfalso


@pytest.fixture
def standard_env() -> Environment:
    return Environment.standard()


def test_exfalso_replaces_goal_with_false(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    exfalso(manager)

    current_goal = manager.current_state.current_goal
    assert current_goal is not None
    assert current_goal.statement == EConst("False", ())


def test_exfalso_requires_active_goal() -> None:
    manager = SimpleNamespace(is_closed=False, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        exfalso(manager)


def test_exfalso_rejects_closed_manager() -> None:
    manager = SimpleNamespace(is_closed=True, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        exfalso(manager)
