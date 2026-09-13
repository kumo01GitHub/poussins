"""Tactic for specializing a hypothesis with an argument (specialize h a)."""
from __future__ import annotations

from ..ast import EMetaVar, EPi, EVar, Expr
from ..ast.ops import substitute_expr_var
from ..errors import TacticError
from ..kernel import Goal, ProofManager
from .helpers import (
    build_app,
    build_lambda_chain,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def specialize(manager: ProofManager, hyp_name: str, arg: Expr) -> None:
    """Specialize hypothesis h with argument a to h : B[x := a].

    Transform context:
        Context, h : Π x : A, B |- G
    To:
        Context, h : B[x := a] |- G
    """
    current_goal = require_current_goal(manager)

    if hyp_name not in current_goal.context:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in local context.")

    hyp_type = current_goal.context[hyp_name]

    if not isinstance(hyp_type, EPi):
        raise TacticError(
            f"Cannot specialize '{hyp_name}': "
            + f"type '{hyp_type}' is not a Pi/function type."
        )

    specialized_type = (
        hyp_type.body
        if hyp_type.var == "_"
        else substitute_expr_var(hyp_type.body, hyp_type.var, arg)
    )

    new_context = current_goal.context | {hyp_name: specialized_type}
    new_goal = Goal(
        statement=current_goal.statement,
        context=new_context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    cut_lambda = build_lambda_chain(
        [(hyp_name, specialized_type)],
        EMetaVar(new_goal.id),
    )
    assignment_expr = build_app(cut_lambda, build_app(EVar(hyp_name), arg))

    manager.refine_goal(assignment_expr, [new_goal])
