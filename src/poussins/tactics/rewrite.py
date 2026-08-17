"""
Advanced Rewrite tactic for equality substitution supporting direction (symm) and location (at).
"""
from __future__ import annotations

from typing import Optional

from ..ast import EApp, EConst, ELam, EMetaVar, EPi, EVar, Expr, UnivLevelParam
from ..environment.library import EqualityDeclaration
from ..errors import TacticError
from ..kernel import ProofManager, whnf
from ..kernel.goal import Goal


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


def _mk_app(fn: Expr, *args: Expr) -> Expr:
    """Helper to chain EApp applications cleanly."""
    res = fn
    for arg in args:
        res = EApp(res, arg)
    return res


def rewrite(
    manager: ProofManager,
    hyp_name: str,
    *,
    symm: bool = False,
    at: Optional[str] = None,
) -> None:
    """
    Advanced rewrite tactic supporting:
    - Direction control (symm=True for reversed substitution, i.e., RHS -> LHS)
    - Location targeting (at='h2' to rewrite inside a local hypothesis instead of the goal)
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
    definitions = manager.engine.env  # Environmentを利用

    hyp_type = whnf(hyp_type_raw, metavars, definitions)

    eq_decl = EqualityDeclaration.EQ_DECLARATION
    eq_name = eq_decl.declaration.name
    # 文字列リストを UnivLevelParam に変換する
    eq_levels = tuple(UnivLevelParam(p) for p in eq_decl.declaration.level_params)

    raw_args = []
    head_expr = hyp_type
    while isinstance(head_expr, EApp):
        raw_args.append(head_expr.arg)
        head_expr = head_expr.fn

    args = list(reversed(raw_args))
    head_name = head_expr.name if isinstance(head_expr, EConst) else None

    if head_name != eq_name or len(args) < 3:
        raise TacticError(f"rewrite failed: Hypothesis '{hyp_name}' is not an equality.")

    eq_type, lhs, rhs = args[0], args[1], args[2]
    from_expr, to_expr = (rhs, lhs) if symm else (lhs, rhs)

    if at is not None:
        if not current_goal.has_local_hypothesis(at):
            raise TacticError(f"rewrite failed: Target hypothesis '{at}' for 'at' modifier not found.")
        target_expr = current_goal.local_context[at]
    else:
        target_expr = current_goal.statement

    new_target_expr = _replace_expr(target_expr, from_expr, to_expr)

    if target_expr == new_target_expr:
        raise TacticError("rewrite failed: Did not find occurrences of the target expression.")

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

    try:
        rec_decl = EqualityDeclaration.EQ_REC_DECLARATION
        rec_levels = tuple(UnivLevelParam(p) for p in rec_decl.declaration.level_params)
        eq_rec_const = EConst(name=rec_decl.declaration.name, levels=rec_levels)

        y_var = "_y"
        h_var = "_h"
        body_with_y = _replace_expr(target_expr, from_expr, EVar(y_var))

        eq_const = EConst(name=eq_name, levels=eq_levels)
        eq_lhs_y = _mk_app(eq_const, eq_type, from_expr, EVar(y_var))

        motive = ELam(y_var, eq_type, ELam(h_var, eq_lhs_y, body_with_y))
        subgoal_placeholder = EMetaVar(new_goal.id)

        assignment = _mk_app(
            eq_rec_const,
            eq_type,
            from_expr,
            motive,
            subgoal_placeholder,
            to_expr,
            EVar(hyp_name),
        )

        manager.refine_goal(assignment, [new_goal])

    except Exception as e:
        raise TacticError(f"rewrite failed: {e}") from e


# Alias
rw = rewrite
