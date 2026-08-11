from types import SimpleNamespace

import pytest

from poussins.ast import EApp, EConst, EMetaVar, EPi, ESort, EVar, UnivLevelZero
from poussins.environment import Environment
from poussins.environment.declaration import ConstructorDeclaration, InductiveDeclaration
from poussins.errors import TacticError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_manager import ProofManager
from poussins.tactics import induction


def test_induction_splits_nat_goal_into_base_and_step_cases() -> None:
    env = Environment.standard()
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"n": EConst("Nat", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    induction(manager, "n")

    assert manager.current_state.current_goal is not None
    assert len(manager.current_state.goals) == 2
    assert any("ih" in goal.context for goal in manager.current_state.goals)


def test_induction_rejects_unknown_hypothesis_name() -> None:
    env = Environment.standard()
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        induction(manager, "missing")


def test_induction_rejects_non_nat_context() -> None:
    env = Environment.standard()
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"n": EConst("False", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    try:
        induction(manager, "n")
    except TacticError:
        pass
    else:
        raise AssertionError("induction should reject non-Nat hypotheses")


def test_induction_rejects_non_inductive_app_head() -> None:
    env = Environment.standard()
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"x": EApp(EConst("False", ()), EConst("True", ()))})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        induction(manager, "x")


def test_induction_rejects_unnamed_head() -> None:
    env = Environment.standard()
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"x": EVar("h")})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        induction(manager, "x")


def test_induction_supports_general_inductive_types() -> None:
    env = Environment.standard()
    env.add(InductiveDeclaration(name="Foo", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("Foo.zero", "Foo.succ")))
    env.add(ConstructorDeclaration(name="Foo.zero", level_params=(), inductive_name="Foo", type=EConst("Foo", ())))
    env.add(ConstructorDeclaration(name="Foo.succ", level_params=(), inductive_name="Foo", type=EPi("x", EConst("Foo", ()), EConst("Foo", ()))))

    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"x": EConst("Foo", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    induction(manager, "x")

    assert manager.current_state.current_goal is not None
    assert len(manager.current_state.goals) == 2
    assert any("ih" in goal.context for goal in manager.current_state.goals)


def test_induction_rejects_closed_manager() -> None:
    manager = SimpleNamespace(is_closed=True, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        induction(manager, "x")


def test_induction_rejects_missing_goal() -> None:
    manager = SimpleNamespace(is_closed=False, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        induction(manager, "x")


def test_induction_rejects_head_without_name() -> None:
    manager = SimpleNamespace(
        is_closed=False,
        current_state=SimpleNamespace(current_goal=Goal(statement=ESort(UnivLevelZero()), context={"x": ESort(UnivLevelZero())}), metavars={}),
        engine=SimpleNamespace(definitions={}),
    )

    with pytest.raises(TacticError):
        induction(manager, "x")


def test_induction_rejects_non_inductive_head() -> None:
    env = Environment.standard()
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"x": EConst("False", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        induction(manager, "x")


def test_induction_rejects_missing_constructor_declaration() -> None:
    env = Environment.standard()
    env.add(InductiveDeclaration(name="Bar", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("Bar.intro",)))
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"x": EConst("Bar", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        induction(manager, "x")


def test_induction_rejects_inductive_type_without_constructors() -> None:
    env = Environment.standard()
    env.add(InductiveDeclaration(name="Baz", level_params=(), type=ESort(UnivLevelZero()), constructor_names=()))
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"x": EConst("Baz", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        induction(manager, "x")


def test_induction_skips_induction_hypothesis_for_non_matching_argument() -> None:
    env = Environment.standard()
    env.add(InductiveDeclaration(name="Qux", level_params=(), type=ESort(UnivLevelZero()), constructor_names=("Qux.mk",)))
    env.add(ConstructorDeclaration(name="Qux.mk", level_params=(), inductive_name="Qux", type=EPi("x", EConst("Bool", ()), EConst("Qux", ()))))
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"x": EConst("Qux", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    induction(manager, "x")

    assert manager.current_state.current_goal is not None
