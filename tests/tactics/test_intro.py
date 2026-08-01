from types import SimpleNamespace

import pytest

from poussins.ast import EConst, ESort, EPi, UnivLevelZero
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_manager import ProofManager
from poussins.tactics.intro import intro, intros


@pytest.fixture
def default_env() -> Environment:
    return Environment.default()


def test_intro_adds_variable_to_context(default_env: Environment) -> None:
    manager = ProofManager(EPi("x", ESort(UnivLevelZero()), ESort(UnivLevelZero())), default_env)

    intro(manager, "h")

    current_goal = manager.current_state.current_goal
    assert current_goal is not None
    assert current_goal.statement == ESort(UnivLevelZero())
    assert current_goal.context["h"] == ESort(UnivLevelZero())


def test_intro_rejects_duplicate_variable_name(default_env: Environment) -> None:
    manager = ProofManager(EPi("x", ESort(UnivLevelZero()), ESort(UnivLevelZero())), default_env)

    intro(manager, "x")

    with pytest.raises(TacticError):
        intro(manager, "x")


def test_intros_adds_multiple_variables(default_env: Environment) -> None:
    goal = EPi("x", ESort(UnivLevelZero()), EPi("y", ESort(UnivLevelZero()), ESort(UnivLevelZero())))
    manager = ProofManager(goal, default_env)

    intros(manager, ["h1", "h2"])

    current_goal = manager.current_state.current_goal
    assert current_goal is not None
    assert current_goal.context["h1"] == ESort(UnivLevelZero())
    assert current_goal.context["h2"] == ESort(UnivLevelZero())


def test_intro_rejects_non_product_goal(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)

    with pytest.raises(TacticError):
        intro(manager, "h")


def test_intro_requires_active_goal() -> None:
    manager = SimpleNamespace(is_closed=False, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        intro(manager, "h")


def test_intro_rejects_closed_manager() -> None:
    manager = SimpleNamespace(is_closed=True, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        intro(manager, "h")


def test_intro_rejects_duplicate_context_name() -> None:
    manager = SimpleNamespace(
        is_closed=False,
        current_state=SimpleNamespace(
            current_goal=Goal(statement=EPi("x", ESort(UnivLevelZero()), ESort(UnivLevelZero())), context={"h": ESort(UnivLevelZero())}),
            metavars={},
        ),
    )

    with pytest.raises(TacticError):
        intro(manager, "h")
