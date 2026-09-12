"""Unit tests for `poussins.tactics.helpers`."""
from __future__ import annotations

import pytest

from poussins.ast import EApp, EConst, ELam, EVar
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.framework import Example, Prop
from poussins.tactics.helpers import (
    build_app,
    build_lambda_chain,
    const_head_name,
    flatten_app_chain,
    fresh_binder_name,
    match_const_app,
    require_current_goal,
    requires_active_goal,
    split_eq_app,
)


class TestRequireCurrentGoal:
    """Tests for active-goal checks."""

    def test_returns_current_goal_when_active(self):
        """Returns the active current goal."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")

        goal = require_current_goal(proof.manager)

        assert goal == proof.current_state.current_goal

    def test_raises_default_message_when_no_active_goal(self):
        """Raises default message when all goals are closed."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")
        proof.exact("hP")

        with pytest.raises(TacticError, match="No active goals remain."):
            require_current_goal(proof.manager)

    def test_raises_tactic_specific_message_when_no_active_goal(self):
        """Raises tactic-scoped message when tactic name is provided."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")
        proof.exact("hP")

        with pytest.raises(TacticError, match="exact failed: No active goals remain."):
            require_current_goal(proof.manager, tactic_name="exact")


class TestRequiresActiveGoalDecorator:
    """Tests for `requires_active_goal` decorator behavior."""

    def test_allows_execution_when_goal_is_active(self):
        """Allows wrapped function execution while a goal is active."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")

        @requires_active_goal
        def dummy_tactic(manager, value: int) -> int:
            return value + 1

        value = 41
        assert dummy_tactic(proof.manager, value) == value + 1

    def test_raises_tactic_error_with_wrapped_function_name(self):
        """Raises with wrapped function name when no active goal remains."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")
        proof.exact("hP")

        @requires_active_goal
        def dummy_tactic(manager) -> None:
            return None

        with pytest.raises(
            TacticError,
            match="dummy_tactic failed: No active goals remain.",
        ):
            dummy_tactic(proof.manager)


class TestFreshBinderName:
    """Tests for fresh binder generation."""

    def test_returns_base_when_name_is_available(self):
        """Keeps base name when there is no collision."""
        name = fresh_binder_name("h", {"x": EVar("X")}, {"y"})
        assert name == "h"

    def test_appends_counter_until_fresh(self):
        """Appends an increasing suffix until the name is fresh."""
        name = fresh_binder_name("h", {"h": EVar("X"), "h1": EVar("X")}, {"h2"})
        assert name == "h3"


class TestBuildApp:
    """Tests for left-associated application construction."""

    def test_builds_left_associated_application(self):
        """Builds nested applications in left-associated order."""
        expr = build_app(EVar("f"), EVar("a"), EVar("b"))
        assert expr == EApp(EApp(EVar("f"), EVar("a")), EVar("b"))

    def test_returns_function_when_no_arguments(self):
        """Returns the input function when no arguments are supplied."""
        expr = build_app(EVar("f"))
        assert expr == EVar("f")


class TestBuildLambdaChain:
    """Tests for nested lambda construction."""

    def test_builds_lambdas_in_binding_order(self):
        """Builds lambdas in the same order as the binding list."""
        expr = build_lambda_chain(
            [("x", EVar("A")), ("y", EVar("B"))],
            EVar("body"),
        )
        expected = ELam("x", EVar("A"), ELam("y", EVar("B"), EVar("body")))
        assert expr == expected

    def test_returns_body_when_binders_are_empty(self):
        """Returns body unchanged when binders are empty."""
        body = EVar("body")
        assert build_lambda_chain([], body) == body


class TestFlattenAppChain:
    """Tests for application-chain decomposition."""

    def test_splits_head_and_arguments(self):
        """Splits application chain into head and ordered arguments."""
        expr = EApp(EApp(EVar("f"), EVar("a")), EVar("b"))
        head, args = flatten_app_chain(expr)
        assert head == EVar("f")
        assert args == (EVar("a"), EVar("b"))

    def test_returns_expr_and_empty_args_for_non_application(self):
        """Returns input as head and empty args for non-application."""
        head, args = flatten_app_chain(EVar("x"))
        assert head == EVar("x")
        assert args == ()


class TestConstHeadName:
    """Tests for extracting constant head names."""

    def test_returns_name_for_constant_head_application(self):
        """Extracts constant name when the application head is EConst."""
        expr = EApp(EConst("True", ()), EVar("x"))
        assert const_head_name(expr) == "True"

    def test_returns_none_when_head_is_not_constant(self):
        """Returns None when the application head is not a constant."""
        expr = EApp(EVar("f"), EVar("x"))
        assert const_head_name(expr) is None


class TestMatchConstApp:
    """Tests for constant-application shape matching."""

    def test_matches_name_and_arity(self):
        """Returns ordered args when constant name and arity match."""
        expr = EApp(EApp(EConst("Or", ()), EVar("p")), EVar("q"))
        args = match_const_app(expr, "Or", 2)
        assert args == (EVar("p"), EVar("q"))

    def test_returns_none_on_name_or_arity_mismatch(self):
        """Returns None on constant name or arity mismatch."""
        expr = EApp(EApp(EConst("Or", ()), EVar("p")), EVar("q"))
        assert match_const_app(expr, "And", 2) is None
        assert match_const_app(expr, "Or", 1) is None

    def test_returns_none_when_head_is_not_constant(self):
        """Returns None when application head is not EConst."""
        expr = EApp(EVar("f"), EVar("x"))
        assert match_const_app(expr, "f", 1) is None


class TestSplitEqApp:
    """Tests for decoding Eq applications."""

    def test_decodes_eq_application_with_three_arguments(self):
        """Decodes `Eq A lhs rhs` into a 3-tuple."""
        expr = EApp(
            EApp(EApp(EConst("Eq", ()), EVar("A")), EVar("lhs")),
            EVar("rhs"),
        )
        assert split_eq_app(expr) == (EVar("A"), EVar("lhs"), EVar("rhs"))

    def test_returns_none_for_non_eq_or_wrong_arity(self):
        """Returns None for non-Eq heads or incomplete Eq applications."""
        not_eq = EApp(EApp(EConst("And", ()), EVar("p")), EVar("q"))
        wrong_arity = EApp(EApp(EConst("Eq", ()), EVar("A")), EVar("lhs"))
        assert split_eq_app(not_eq) is None
        assert split_eq_app(wrong_arity) is None
