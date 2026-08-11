"""
Rewrite tactic for equality substitution.
"""
from __future__ import annotations

from ..ast import EApp, EConst, ELam, EPi, Expr
from ..environment.library import EqualityDeclaration
from ..errors import TacticError
from ..kernel import ProofManager, whnf


def _replace_expr(expr: Expr, target: Expr, replacement: Expr) -> Expr:
    """Recursively replace occurrences of `target` with `replacement` in `expr`."""
    if expr == target:
        return replacement

    if isinstance(expr, EApp):
        fn = _replace_expr(expr.fn, target, replacement)
        arg = _replace_expr(expr.arg, target, replacement)
        return EApp(fn, arg)

    if isinstance(expr, ELam):
        body = _replace_expr(expr.body, target, replacement)
        var_type = _replace_expr(expr.var_type, target, replacement)
        return ELam(expr.var_name, var_type, body)

    if isinstance(expr, EPi):
        body = _replace_expr(expr.body, target, replacement)
        var_type = _replace_expr(expr.var_type, target, replacement)
        return EPi(expr.var_name, var_type, body)

    return expr


def rewrite(manager: ProofManager, hyp_name: str) -> None:
    """
    Rewrites occurrences of LHS with RHS in the current goal using an equality hypothesis.
    """
    if manager.is_closed:
        raise TacticError("rewrite failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    if current_goal is None:
        raise TacticError("rewrite failed: No active goals remain.")

    if not current_goal.has_local_hypothesis(hyp_name):
        raise TacticError(f"rewrite failed: Hypothesis '{hyp_name}' not found in local context.")

    hyp_type_raw = current_goal.local_context[hyp_name]
    metavars = state.metavars
    definitions = manager.engine.definitions

    hyp_type = whnf(hyp_type_raw, metavars, definitions)

    raw_args = []
    head_expr = hyp_type
    while isinstance(head_expr, EApp):
        raw_args.append(head_expr.arg)
        head_expr = head_expr.fn

    args = list(reversed(raw_args))
    head_name = head_expr.name if isinstance(head_expr, EConst) else None
    eq_name = EqualityDeclaration.EQ_DECLARATION.declaration.name

    if head_name != eq_name or len(args) < 3:
        raise TacticError(f"rewrite failed: Hypothesis '{hyp_name}' is not an equality.")

    lhs, rhs = args[1], args[2]

    goal_target = current_goal.statement
    new_target = _replace_expr(goal_target, lhs, rhs)

    if goal_target == new_target:
        raise TacticError(f"rewrite failed: Did not find occurrences of LHS in current goal.")

    manager.change_goal(new_target)


# Alias
rw = rewrite
