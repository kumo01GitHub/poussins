"""Kernel-level evaluation functions for expressions."""
from __future__ import annotations

from ..ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
    substitute_expr_var,
    substitute_metavar,
)
from ..environment import DefinitionDeclaration, Environment
from .proof_state import MetaVar


def instantiate_metavar(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """Instantiate assigned metavariables in an expression."""
    current = expr
    for goal_id, metavar in metavars.items():
        if metavar.is_assigned:
            current = substitute_metavar(current, goal_id, metavar.assignment)
    return current


def instantiate(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """Recursively replace all assigned metavariables in an expression."""
    current = expr
    while True:
        next_term = instantiate_metavar(current, metavars)
        if next_term == current:
            break
        current = next_term
    return current


def whnf(
    expr: Expr,
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
    unfolding: frozenset[str] | None = None,
) -> Expr:
    """Reduce an expression to weak head normal form."""
    if unfolding is None:
        unfolding = frozenset()

    expr = instantiate_metavar(expr, metavars)
    match expr:
        case EConst(name, _):
            if env is not None and name not in unfolding:
                decl = env.get(name)
                if isinstance(decl, DefinitionDeclaration):
                    return whnf(decl.value, metavars, env, unfolding | {name})
            return expr
        case EApp(fn, arg):
            fn_whnf = whnf(fn, metavars, env, unfolding)
            if isinstance(fn_whnf, ELam):
                new_expr = substitute_expr_var(fn_whnf.body, fn_whnf.var, arg)
                return whnf(new_expr, metavars, env, unfolding)
            return EApp(fn_whnf, arg)
        case (
            ESort(_)
            | EVar(_)
            | ELam(_, _, _)
            | EPi(_, _, _)
            | EMatch(_, _, _, _)
            | EMetaVar(_)
        ):
            return expr
        case _:
            raise NotImplementedError(f"whnf not implemented for {type(expr).__name__}")
