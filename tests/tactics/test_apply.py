"""Contract and behavior tests for `poussins.tactics.apply`."""
from __future__ import annotations

import pytest

from poussins.ast import EVar
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.framework import Example, Prop
from poussins.tactics import apply


class TestApplyTactic:
    """`apply` common contracts and tactic-specific behavior."""

    def test_updates_goal_to_premise_subgoal(self):
        """Success: `hPQ : P -> Q` on goal `Q` creates subgoal `P`."""
        env = Environment.standard()
        p, q = Prop("P", env), Prop("Q", env)
        proof = Example((p >> q) >> (p >> q), env)
        proof.intros(["hPQ", "hP"])

        before = proof.current_state
        apply(proof.manager, EVar("hPQ"))

        after = proof.current_state
        assert proof.is_closed or after != before
        assert proof.is_closed is False
        current_goal = proof.current_state.current_goal
        assert current_goal is not None
        assert current_goal.statement == p.expr
        assert len(proof.current_state.goals) == 1

    def test_raises_tactic_error_when_no_active_goal(self):
        """Failure: `apply` raises `TacticError` when no goal is active."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")
        proof.exact("hP")
        before = proof.current_state

        with pytest.raises(
            TacticError,
            match="apply failed: No active goals remain.",
        ):
            apply(proof.manager, EVar("hP"))

        assert proof.current_state == before
        assert proof.is_closed
