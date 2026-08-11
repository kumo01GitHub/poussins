from types import SimpleNamespace

import pytest

from poussins.ast import EApp, EConst, ESort, UnivLevelZero
from poussins.environment import Environment
from poussins.environment.declaration import ConstantDeclaration, ConstructorDeclaration, InductiveDeclaration
from poussins.errors import TacticError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_manager import ProofManager
from poussins.tactics.constructor import constructor, left, right, split


@pytest.fixture
def standard_env() -> Environment:
    return Environment.standard()


def test_constructor_applies_matching_constructor_to_inductive_goal(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    constructor(manager)

    assert manager.is_closed
    assert manager.current_proof_term == EConst("True.intro", ())


def test_constructor_handles_constructor_with_pi_bindings(standard_env: Environment) -> None:
    manager = ProofManager(EApp(EApp(EConst("And", ()), EConst("True", ())), EConst("True", ())), standard_env)

    constructor(manager)

    assert manager.current_state.current_goal is not None


def test_constructor_with_index_selects_named_constructor(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    constructor(manager, index=1)

    assert manager.is_closed
    assert manager.current_proof_term == EConst("True.intro", ())


def test_left_applies_or_left_constructor(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    with pytest.raises(TacticError):
        left(manager)


def test_right_applies_or_right_constructor(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    with pytest.raises(TacticError):
        right(manager)


def test_split_applies_and_constructor(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    with pytest.raises(TacticError):
        split(manager)


def test_constructor_requires_active_goal() -> None:
    manager = SimpleNamespace(is_closed=False, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(AssertionError):
        constructor(manager)


def test_constructor_rejects_closed_manager() -> None:
    manager = SimpleNamespace(is_closed=True, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        constructor(manager)


def test_constructor_rejects_goal_without_inductive_head(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)
    original_goal = manager.current_state.current_goal
    assert original_goal is not None
    mutated_goal = Goal(statement=ESort(UnivLevelZero()), context=original_goal.context)
    manager.session._history[-1] = manager.session._history[-1].__class__(
        goals=(mutated_goal,),
        metavars=manager.current_state.metavars,
    )

    with pytest.raises(TacticError):
        constructor(manager)


def test_constructor_rejects_non_inductive_head(standard_env: Environment) -> None:
    env = Environment.standard()
    env.add(ConstantDeclaration(name="Foo", level_params=(), type=ESort(UnivLevelZero()), value=None))
    manager = ProofManager(EConst("Foo", ()), env)

    with pytest.raises(TacticError):
        constructor(manager)


def test_constructor_rejects_inductive_type_without_constructors(standard_env: Environment) -> None:
    env = Environment.standard()
    env.add(InductiveDeclaration(name="Foo", level_params=(), type=ESort(UnivLevelZero()), constructor_names=()))
    manager = ProofManager(EConst("Foo", ()), env)

    with pytest.raises(TacticError):
        constructor(manager)


def test_constructor_rejects_invalid_index(standard_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), standard_env)

    with pytest.raises(TacticError):
        constructor(manager, index=2)


def test_constructor_rejects_missing_indexed_constructor_declaration(standard_env: Environment) -> None:
    env = Environment.standard()
    env.add(InductiveDeclaration(name="Foo", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("Foo.intro",)))
    manager = ProofManager(EConst("Foo", ()), env)

    with pytest.raises(TacticError):
        constructor(manager, index=1)


def test_constructor_rejects_constructor_without_constructor_declaration(standard_env: Environment) -> None:
    env = Environment.standard()
    env.add(InductiveDeclaration(name="Foo", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("Foo.intro",)))
    env.add(ConstantDeclaration(name="Foo.intro", level_params=(), type=EConst("Foo", ()), value=None))
    manager = ProofManager(EConst("Foo", ()), env)

    with pytest.raises(TacticError):
        constructor(manager)


def test_constructor_rejects_unmatched_constructor(standard_env: Environment) -> None:
    env = Environment.standard()
    env.add(InductiveDeclaration(name="Foo", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("Foo.intro",)))
    env.add(ConstructorDeclaration(name="Foo.intro", level_params=(), inductive_name="Foo", type=EConst("Bar", ())))
    manager = ProofManager(EConst("Foo", ()), env)

    with pytest.raises(TacticError):
        constructor(manager)


def test_left_right_and_split_raise_for_missing_inductive_declarations(standard_env: Environment) -> None:
    env = Environment.standard()
    env.declarations.pop("Or", None)
    env.add(ConstantDeclaration(name="Or", level_params=(), type=ESort(UnivLevelZero()), value=None))
    manager = ProofManager(EConst("Or", ()), env)

    with pytest.raises(TacticError):
        left(manager)

    with pytest.raises(TacticError):
        right(manager)


def test_left_right_and_split_raise_for_missing_constructor_names(standard_env: Environment) -> None:
    env = Environment.standard()
    env.declarations.pop("And", None)
    env.add(InductiveDeclaration(name="And", level_params=(), type=ESort(UnivLevelZero()), constructor_names=()))
    manager = ProofManager(EConst("And", ()), env)

    with pytest.raises(TacticError):
        split(manager)


def test_left_right_and_split_raise_for_closed_manager() -> None:
    manager = SimpleNamespace(is_closed=True, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        left(manager)

    with pytest.raises(TacticError):
        right(manager)

    with pytest.raises(TacticError):
        split(manager)


def test_left_rejects_constructor_name_not_in_inductive_declarations() -> None:
    env = Environment.standard()
    env.declarations.pop("Or", None)
    env.add(InductiveDeclaration(name="Or", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("Or.inr",)))
    manager = ProofManager(EConst("Or", ()), env)

    with pytest.raises(TacticError):
        left(manager)


def test_left_right_and_split_raise_when_current_goal_is_missing() -> None:
    manager = SimpleNamespace(is_closed=False, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        left(manager)

    with pytest.raises(TacticError):
        right(manager)

    with pytest.raises(TacticError):
        split(manager)


def test_goal_head_name_raises_when_head_has_no_name() -> None:
    manager = SimpleNamespace(
        is_closed=False,
        current_state=SimpleNamespace(current_goal=Goal(statement=ESort(UnivLevelZero()), context={}), metavars={}),
        engine=SimpleNamespace(definitions={}),
    )

    with pytest.raises(TacticError):
        from poussins.tactics.constructor import _goal_head_name

        _goal_head_name(manager)


def test_goal_head_name_uses_nested_application() -> None:
    manager = SimpleNamespace(
        is_closed=False,
        current_state=SimpleNamespace(
            current_goal=Goal(statement=EApp(EApp(EConst("And", ()), EConst("True", ())), EConst("True", ())), context={}),
            metavars={},
        ),
        engine=SimpleNamespace(definitions={}),
    )

    from poussins.tactics.constructor import _goal_head_name

    assert _goal_head_name(manager) == "And"


def test_named_constructor_rejects_head_mismatch() -> None:
    env = Environment.standard()
    env.declarations.pop("And", None)
    env.add(InductiveDeclaration(name="And", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("And.intro",)))
    manager = ProofManager(EConst("True", ()), env)

    with pytest.raises(TacticError):
        from poussins.tactics.constructor import _apply_named_constructor

        _apply_named_constructor(manager, inductive_name="And", constructor_name="And.intro", tactic_name="custom")


def test_named_constructor_reaches_apply_path() -> None:
    env = Environment.standard()
    env.declarations.pop("And", None)
    env.declarations.pop("And.intro", None)
    env.add(InductiveDeclaration(name="And", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("And.intro",)))
    env.add(ConstructorDeclaration(name="And.intro", level_params=(), inductive_name="And", type=EConst("And", ())))
    manager = ProofManager(EConst("And", ()), env)

    from poussins.tactics.constructor import _apply_named_constructor

    _apply_named_constructor(manager, inductive_name="And", constructor_name="And.intro", tactic_name="split")


def test_named_constructor_rejects_non_constructor_declaration() -> None:
    class DummyEnv:
        def get(self, name: str):
            if name == "And":
                return InductiveDeclaration(name="And", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("And.intro",))
            if name == "And.intro":
                return ConstantDeclaration(name="And.intro", level_params=(), type=EConst("And", ()), value=None)
            return None

    manager = SimpleNamespace(
        is_closed=False,
        current_state=SimpleNamespace(current_goal=Goal(statement=EConst("And", ()), context={}), metavars={}),
        env=DummyEnv(),
        engine=SimpleNamespace(definitions={})
    )

    from poussins.tactics.constructor import _apply_named_constructor

    with pytest.raises(TacticError):
        _apply_named_constructor(manager, inductive_name="And", constructor_name="And.intro", tactic_name="split")
