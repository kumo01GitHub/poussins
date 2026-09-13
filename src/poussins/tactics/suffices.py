"""Tactic for asserting a sufficient hypothesis (suffices h : P)."""
from __future__ import annotations

from ..ast import EMetaVar, Expr
from ..kernel import Goal, ProofManager
from .helpers import (
    build_app,
    build_lambda_chain,
    fresh_binder_name,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def suffices(manager: ProofManager, hyp_name: str, expr: Expr) -> None:
    """Assert that hypothesis h : P is sufficient to prove current goal G.

    Splits the current goal into:
    1. Context, h : P |- G  (prove main goal using hypothesis h : P)
    2. Context |- P         (prove that P holds)
    """
    current_goal = require_current_goal(manager)

    used_hypothesis_names = (
        set(current_goal.local_hypothesis_names)
        if current_goal.local_hypothesis_names is not None
        else set()
    )
    bound_name = fresh_binder_name(
        hyp_name,
        current_goal.local_context,
        used_hypothesis_names,
    )

    new_context = current_goal.context | {bound_name: expr}
    new_local_hypothesis_names = (
        current_goal.local_hypothesis_names or frozenset()
    ) | {bound_name}

    new_goal = Goal(
        statement=current_goal.statement,
        context=new_context,
        local_hypothesis_names=new_local_hypothesis_names,
    )

    proof_goal = Goal(
        statement=expr,
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    cut_lambda = build_lambda_chain(
        [(bound_name, expr)],
        EMetaVar(new_goal.id),
    )
    assignment_expr = build_app(cut_lambda, EMetaVar(proof_goal.id))

    manager.refine_goal(assignment_expr, [new_goal, proof_goal])
