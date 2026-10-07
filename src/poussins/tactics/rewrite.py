"""Advanced Rewrite tactic for equality substitution (Lean 4 style)."""

from __future__ import annotations

from ..ast import ELam, EMetaVar, EVar, Expr, build_app_chain, substitute_expr
from ..environment.library import EqualityDeclaration
from ..errors import TacticError
from ..kernel import ProofManager, infer_type, whnf
from ..kernel.goal import Goal
from .helpers import (
    const_from_decl,
    parse_eq_app,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def rewrite(
    manager: ProofManager,
    term: Expr,
    symm: bool = False,
    hyp_name: str | None = None,
    subexpr: Expr | None = None,
) -> None:
    """Rewrite using an equality proof term (hypothesis, theorem application, etc.)."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    term_type = infer_type(
        term,
        current_goal.context,
        state.metavars,
        manager.env,
    )

    eq_args = parse_eq_app(whnf(term_type, state.metavars, manager.env))
    if eq_args is None:
        raise TacticError("The provided term is not an equality.")

    eq_type, lhs, rhs = eq_args
    from_expr, to_expr = (rhs, lhs) if symm else (lhs, rhs)

    if hyp_name is not None:
        if not current_goal.has_local_hypothesis(hyp_name):
            raise TacticError(
                f"Target hypothesis '{hyp_name}' for 'hyp_name' modifier not found."
            )
        target_expr = current_goal.local_context[hyp_name]
    else:
        target_expr = current_goal.statement

    if subexpr is not None:
        new_subexpr = substitute_expr(subexpr, from_expr, to_expr)
        if new_subexpr == subexpr:
            raise TacticError(
                "Did not find occurrences of the target expression within 'subexpr'."
            )
        new_target_expr = substitute_expr(target_expr, subexpr, new_subexpr)
    else:
        new_target_expr = substitute_expr(target_expr, from_expr, to_expr)

    if new_target_expr == target_expr:
        raise TacticError("Did not find occurrences of the target expression.")

    if hyp_name is not None:
        new_context = dict(current_goal.context)
        new_context[hyp_name] = new_target_expr
        new_goal = Goal(
            statement=current_goal.statement,
            context=new_context,
            local_hypothesis_names=current_goal.local_hypothesis_names,
        )
    else:
        new_goal = Goal(
            statement=new_target_expr,
            context=current_goal.context,
            local_hypothesis_names=current_goal.local_hypothesis_names,
        )

    y_var = "_y"
    h_var = "_h"

    body_with_y = (
        substitute_expr(
            target_expr,
            subexpr,
            substitute_expr(subexpr, from_expr, EVar(y_var))
        )
        if subexpr is not None
        else substitute_expr(target_expr, from_expr, EVar(y_var))
    )

    eq_lhs_y = build_app_chain(
        const_from_decl(EqualityDeclaration.EQ_DECLARATION.declaration, manager),
        eq_type,
        from_expr,
        EVar(y_var),
    )

    assignment = build_app_chain(
        const_from_decl(EqualityDeclaration.EQ_REC_DECLARATION.declaration, manager),
        eq_type,
        from_expr,
        ELam(y_var, eq_type, ELam(h_var, eq_lhs_y, body_with_y)),
        EMetaVar(new_goal.id),
        to_expr,
        term,
    )

    manager.refine_goal(assignment, [new_goal])


# Alias
rw = rewrite
