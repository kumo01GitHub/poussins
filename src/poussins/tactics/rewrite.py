"""Advanced Rewrite tactic for equality substitution."""
from __future__ import annotations

from ..ast import EApp, EConst, ELam, EMetaVar, EPi, EVar, Expr, UnivLevelParam
from ..environment.library import EqualityDeclaration
from ..errors import TacticError
from ..kernel import ProofManager, whnf
from ..kernel.goal import Goal
from .helpers import build_app, require_current_goal, requires_active_goal, split_eq_app


def _replace_expr(expr: Expr, target: Expr, replacement: Expr) -> Expr:
    """Recursively replace occurrences of `target` with `replacement` in `expr`."""
    if expr == target:
        return replacement

    match expr:
        case EApp(fn, arg):
            return EApp(
                _replace_expr(fn, target, replacement),
                _replace_expr(arg, target, replacement),
            )
        case ELam(var_name, var_type, body):
            return ELam(
                var_name,
                _replace_expr(var_type, target, replacement),
                _replace_expr(body, target, replacement),
            )
        case EPi(var_name, var_type, body):
            return EPi(
                var_name,
                _replace_expr(var_type, target, replacement),
                _replace_expr(body, target, replacement),
            )
        case _:
            return expr


@requires_active_goal
def rewrite(
    manager: ProofManager,
    hyp_name: str,
    *,
    symm: bool = False,
    at: str | None = None,
) -> None:
    """Rewrite occurrences of LHS with RHS in current goal using hypothesis."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    if not current_goal.has_local_hypothesis(hyp_name):
        raise TacticError(f"Hypothesis '{hyp_name}' not found in local context.")

    eq_decl = EqualityDeclaration.EQ_DECLARATION
    eq_name = eq_decl.declaration.name
    eq_levels = tuple(UnivLevelParam(p) for p in eq_decl.declaration.level_params)

    hyp_type = whnf(current_goal.local_context[hyp_name], state.metavars, manager.env)
    eq_args = split_eq_app(hyp_type, eq_name)
    if eq_args is None:
        raise TacticError(f"Hypothesis '{hyp_name}' is not an equality.")

    eq_type, lhs, rhs = eq_args
    from_expr, to_expr = (rhs, lhs) if symm else (lhs, rhs)

    if at is not None:
        if not current_goal.has_local_hypothesis(at):
            raise TacticError(f"Target hypothesis '{at}' for 'at' modifier not found.")
        target_expr = current_goal.local_context[at]
    else:
        target_expr = current_goal.statement

    new_target_expr = _replace_expr(target_expr, from_expr, to_expr)

    if target_expr == new_target_expr:
        raise TacticError("Did not find occurrences of the target expression.")

    if at is not None:
        new_context = dict(current_goal.context)
        new_context[at] = new_target_expr
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

    rec_decl = EqualityDeclaration.EQ_REC_DECLARATION
    rec_levels = tuple(UnivLevelParam(p) for p in rec_decl.declaration.level_params)
    eq_rec_const = EConst(name=rec_decl.declaration.name, levels=rec_levels)

    y_var = "_y"
    h_var = "_h"
    body_with_y = _replace_expr(target_expr, from_expr, EVar(y_var))
    eq_lhs_y = build_app(
        EConst(name=eq_name, levels=eq_levels),
        eq_type,
        from_expr,
        EVar(y_var)
    )

    assignment = build_app(
        eq_rec_const,
        eq_type,
        from_expr,
        ELam(y_var, eq_type, ELam(h_var, eq_lhs_y, body_with_y)),
        EMetaVar(new_goal.id),
        to_expr,
        EVar(hyp_name),
    )

    manager.refine_goal(assignment, [new_goal])


# Alias
rw = rewrite
