"""Tactic for introducing intermediate assertions (have h : P)."""
from __future__ import annotations

from ..ast import (
    EMetaVar,
    EPi,
    EVar,
    Expr,
    build_app_chain,
    build_lambda_chain,
)
from ..kernel import Goal, ProofManager
from .helpers import (
    fresh_binder_name,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def have(manager: ProofManager, name: str, expr: Expr) -> None:
    """Introduce an intermediate assertion (have h : P).

    Splits the current goal into:
    1. Context |- P
    2. Context, h : P |- G
    """
    current_goal = require_current_goal(manager)

    used_hypothesis_names = (
        set(current_goal.local_hypothesis_names)
        if current_goal.local_hypothesis_names is not None
        else set()
    )
    bound_name = fresh_binder_name(
        name,
        current_goal.local_context,
        used_hypothesis_names,
    )

    proof_goal = Goal(
        statement=expr,
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
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

    p_to_g = EPi("_", expr, current_goal.statement)
    cut_fn = build_lambda_chain(
        [("f", p_to_g)],
        build_app_chain(EVar("f"), EMetaVar(proof_goal.id)),
    )
    cut_arg = build_lambda_chain(
        [(bound_name, expr)],
        EMetaVar(new_goal.id),
    )
    assignment_expr = build_app_chain(cut_fn, cut_arg)

    manager.refine_goal(assignment_expr, [proof_goal, new_goal])
