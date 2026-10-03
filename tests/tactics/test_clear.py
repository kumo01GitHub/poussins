"""Contract and behavior tests for `poussins.tactics.clear`."""
from __future__ import annotations

import pytest

from poussins.environment import Environment
from poussins.errors import TacticError
from poussins.framework import Example, Prop
from poussins.tactics import clear


class TestClearTactic:
    """`clear` removes a local hypothesis without altering the target."""

    def test_clears_unused_hypothesis(self):
        """Success: removing an unused local hypothesis updates the local context."""
        env = Environment.standard()
        p, q = Prop("P", env), Prop("Q", env)
        proof = Example(p >> (q >> q), env)
        proof.intros(["hP", "hQ"])

        before = len(proof.manager.session.history)
        clear(proof.manager, "hP")

        assert len(proof.manager.session.history) == before + 1
        current_goal = proof.current_state.current_goal
        assert current_goal is not None
        assert "hP" not in current_goal.local_context
        assert "hQ" in current_goal.local_context
        assert current_goal.statement == q.expr

    def test_raises_tactic_error_when_hypothesis_is_missing(self):
        """Failure: `clear` raises a `TacticError` if the hypothesis is absent."""
        env = Environment.standard()
        p = Prop("P", env)
        proof = Example(p >> p, env)
        proof.intro("hP")

        with pytest.raises(
            TacticError,
            match="Hypothesis 'missing' not found in local context.",
        ):
            clear(proof.manager, "missing")
