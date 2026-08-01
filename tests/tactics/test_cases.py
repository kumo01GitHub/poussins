from types import SimpleNamespace

import pytest

from poussins.ast import EApp, EConst, ELam, EMetaVar, ESort, EVar, EPi, UnivLevelZero
from poussins.environment import Environment
from poussins.environment.declaration import InductiveDeclaration
from poussins.errors import TacticError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_manager import ProofManager
from poussins.tactics import cases as cases_tactic
from poussins.tactics.cases import (
    _build_branch_expr,
    _build_constructor_pattern,
    _collect_pi_binders,
    _fresh_name,
    _infer_inductive_parameter_substitutions,
    cases,
)


@pytest.fixture
def default_env() -> Environment:
    return Environment.default()


def test_cases_splits_on_inductive_hypothesis(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EConst("True", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    cases(manager, "h")

    assert manager.current_state.current_goal is not None
    assert manager.current_state.current_goal.context["h"] == EConst("True", ())


def test_cases_rejects_unknown_hypothesis(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)

    with pytest.raises(TacticError):
        cases(manager, "missing")


def test_cases_rejects_empty_patterns(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EConst("True", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        cases(manager, "h", patterns=((),))


def test_cases_rejects_too_many_branch_names(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EConst("True", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        cases(manager, "h", patterns=(("True.intro", "x", "y"),))


def test_cases_handles_closed_and_missing_goals() -> None:
    manager = SimpleNamespace(is_closed=True, current_state=SimpleNamespace(current_goal=None, metavars={}))

    with pytest.raises(TacticError):
        cases(manager, "h")

    manager = SimpleNamespace(is_closed=False, current_state=SimpleNamespace(current_goal=None, metavars={}))
    with pytest.raises(TacticError):
        cases(manager, "h")


def test_cases_rejects_unknown_hypothesis_head(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": ESort(UnivLevelZero())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        cases(manager, "h")


def test_cases_rejects_non_inductive_hypothesis(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EConst("False", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        cases(manager, "h")


def test_cases_rejects_unknown_inductive_head(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EConst("Missing", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        cases(manager, "h")


def test_cases_rejects_inductive_type_without_constructors(default_env: Environment) -> None:
    env = Environment.default()
    env.add(InductiveDeclaration(name="Foo", level_params=(), type=ESort(UnivLevelZero()), constructor_names=()))
    manager = ProofManager(EConst("True", ()), env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EConst("Foo", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        cases(manager, "h")


def test_cases_rejects_unknown_constructor(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EConst("True", ())})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        cases(manager, "h", patterns=(("missing",),))


def test_cases_handles_nested_application_hypothesis(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(statement=EConst("True", ()), context={"h": EApp(EConst("True", ()), EConst("True", ()))})
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    with pytest.raises(TacticError):
        cases(manager, "h")


def test_cases_handles_branch_binders_and_substitutions(default_env: Environment) -> None:
    manager = ProofManager(EConst("True", ()), default_env)
    subgoal = Goal(
        statement=EConst("True", ()),
        context={"h": EApp(EApp(EConst("And", ()), EConst("True", ())), EConst("True", ()))},
    )
    manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

    cases(manager, "h", patterns=(("And.intro", "ha"),))

    assert manager.current_state.current_goal is not None


def test_cases_helper_functions_cover_branches() -> None:
    context = {"x": EConst("A", ())}
    assert _fresh_name("x", context, set()) == "x1"
    assert _fresh_name("y", context, {"y"}) == "y1"

    constructor_type = EPi("a", EConst("A", ()), EPi("b", EConst("B", ()), EConst("C", ())))
    pattern, binders = _build_constructor_pattern(EConst("Foo", ()), constructor_type, context, set())
    assert isinstance(pattern, EApp)
    assert binders[0][0] == "a"

    assert isinstance(_build_branch_expr([("x", EConst("A", ()))], "g"), ELam)
    assert _collect_pi_binders(constructor_type) == ["a", "b"]

    substitutions = _infer_inductive_parameter_substitutions(EVar("x"), EVar("y"))
    assert substitutions == {"x": EVar("y")}

    with pytest.raises(TacticError):
        _infer_inductive_parameter_substitutions(EConst("A", ()), EConst("B", ()))

    assert _infer_inductive_parameter_substitutions(EVar("x"), EConst("A", ())) == {"x": EConst("A", ())}

    assert _infer_inductive_parameter_substitutions(EConst("A", ()), EConst("A", ())) == {}
    assert _infer_inductive_parameter_substitutions(EApp(EConst("A", ()), EVar("x")), EApp(EConst("A", ()), EVar("y"))) == {"x": EVar("y")}
    assert _infer_inductive_parameter_substitutions(ESort(UnivLevelZero()), ESort(UnivLevelZero())) == {}
    assert _infer_inductive_parameter_substitutions(EPi("x", EConst("A", ()), EConst("B", ())), EPi("y", EConst("A", ()), EConst("B", ()))) == {}
    assert _infer_inductive_parameter_substitutions(ELam("x", EConst("A", ()), EConst("B", ())), ELam("y", EConst("A", ()), EConst("B", ()))) == {}
    assert _infer_inductive_parameter_substitutions(EMetaVar("g"), EMetaVar("g")) == {}

    with pytest.raises(TacticError):
        _infer_inductive_parameter_substitutions(EMetaVar("g"), EMetaVar("h"))

    with pytest.raises(TacticError):
        _infer_inductive_parameter_substitutions(EApp(EConst("A", ()), EVar("x")), EConst("B", ()))

    assert cases_tactic is not None
