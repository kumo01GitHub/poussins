"""Tactic for introducing intermediate assertions (have h : P)."""
from __future__ import annotations

from ..ast import EMetaVar, EPi, EVar, Expr
from ..kernel import Goal, ProofManager
from .helpers import (
    build_app,
    build_lambda_chain,
    fresh_binder_name,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def have(manager: ProofManager, var_name: str, proof_type: Expr) -> None:
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
        var_name,
        current_goal.local_context,
        used_hypothesis_names,
    )

    proof_goal = Goal(
        statement=proof_type,
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    new_context = current_goal.context | {bound_name: proof_type}
    new_local_hypothesis_names = (
        current_goal.local_hypothesis_names or frozenset()
    ) | {bound_name}

    main_goal = Goal(
        statement=current_goal.statement,
        context=new_context,
        local_hypothesis_names=new_local_hypothesis_names,
    )

    p_to_g = EPi("_", proof_type, current_goal.statement)
    cut_fn = build_lambda_chain(
        [("f", p_to_g)],
        build_app(EVar("f"), EMetaVar(proof_goal.id)),
    )
    cut_arg = build_lambda_chain(
        [(bound_name, proof_type)],
        EMetaVar(main_goal.id),
    )
    assignment_expr = build_app(cut_fn, cut_arg)

    manager.refine_goal(assignment_expr, [proof_goal, main_goal])
