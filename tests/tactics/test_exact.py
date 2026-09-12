"""Contract and behavior tests for `poussins.tactics.exact`."""
from __future__ import annotations

import pytest

from poussins.ast import ELam, EVar
from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.framework import Example, Prop
from poussins.tactics import exact


class TestExactTactic:
    """`exact` common contracts and tactic-specific behavior."""

    def test_closes_goal_and_uses_given_witness(self):
        """Success: closes the current goal with the provided term."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")

        before = proof.current_state
        exact(proof.manager, EVar("hP"))

        after = proof.current_state
        assert proof.is_closed or after != before
        assert proof.is_closed
        assert proof.manager.current_proof_term == ELam("hP", p.expr, EVar("hP"))

    def test_raises_tactic_error_when_no_active_goal(self):
        """Failure: `exact` raises `TacticError` when no goal is active."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")
        exact(proof.manager, EVar("hP"))
        before = proof.current_state

        with pytest.raises(
            TacticError,
            match="exact failed: No active goals remain.",
        ):
            exact(proof.manager, EVar("hP"))

        assert proof.current_state == before
        assert proof.is_closed
