"""Tactics for simplifying expressions in the current goal or hypothesis."""
from __future__ import annotations

from ..kernel.eval import normalize
from ..kernel.proof_manager import ProofManager
from .helpers import require_current_goal, requires_active_goal


@requires_active_goal
def simpl(
    manager: ProofManager,
    hyp_name: str | None = None,
    unfolding: frozenset[str] | None = None,
) -> None:
    """Simplify the current goal or a local hypothesis by fully evaluating its terms."""
    current_goal = require_current_goal(manager, tactic_name="simpl")
    metavars = manager.current_state.metavars
    env = manager.env

    if hyp_name is None:
        target_expr = current_goal.statement
        new_expr = normalize(
            target_expr, metavars=metavars, env=env, unfolding=unfolding
        )
        manager.change_goal(new_expr)
    else:
        hypothesis_expr = current_goal.context[hyp_name]
        new_expr = normalize(
            hypothesis_expr, metavars=metavars, env=env, unfolding=unfolding
        )
        manager.change_hypothesis(hyp_name, new_expr)


@requires_active_goal
def dsimp(
    manager: ProofManager,
    hyp_name: str | None = None,
    unfolding: frozenset[str] | None = None,
) -> None:
    """Definitional simplify without expanding unnecessary definitions."""
    simpl(manager, hyp_name=hyp_name, unfolding=unfolding)


@requires_active_goal
def unfold(
    manager: ProofManager,
    name: str,
    hyp_name: str | None = None,
) -> None:
    """Unfold a specific definition in the current goal or hypothesis."""
    simpl(
        manager,
        hyp_name=hyp_name,
        unfolding=frozenset([name]),
    )
