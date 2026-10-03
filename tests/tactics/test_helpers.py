"""Unit tests for `poussins.tactics.helpers`."""
from __future__ import annotations

import pytest

from poussins.ast import EApp, EConst, EVar
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.framework import Example, Prop
from poussins.tactics.helpers import (
    const_head_name,
    fresh_binder_name,
    parse_eq_app,
    require_current_goal,
    requires_active_goal,
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


class TestParseEqApp:
    """Tests for decoding Eq applications."""

    def test_decodes_eq_application_with_three_arguments(self):
        """Decodes `Eq A lhs rhs` into a 3-tuple."""
        expr = EApp(
            EApp(EApp(EConst("Eq", ()), EVar("A")), EVar("lhs")),
            EVar("rhs"),
        )
        assert parse_eq_app(expr) == (EVar("A"), EVar("lhs"), EVar("rhs"))

    def test_returns_none_for_non_eq_or_wrong_arity(self):
        """Returns None for non-Eq heads or incomplete Eq applications."""
        not_eq = EApp(EApp(EConst("And", ()), EVar("p")), EVar("q"))
        wrong_arity = EApp(EApp(EConst("Eq", ()), EVar("A")), EVar("lhs"))
        assert parse_eq_app(not_eq) is None
        assert parse_eq_app(wrong_arity) is None
