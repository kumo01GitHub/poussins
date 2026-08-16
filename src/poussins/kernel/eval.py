"""
Kernel-level evaluation functions for expressions, including weak head normal form reduction and metavariable instantiation.
"""
from __future__ import annotations
from collections.abc import Mapping

from .proof_state import MetaVar
from ..ast import (
    Expr, EConst, EApp, ELam,
    substitute_metavar, substitute_expr_var
)


Definitions = Mapping[str, Expr | None] | None


def instantiate_metavar(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """
    Instantiate assigned metavariables in an expression.
    """
    current = expr
    for goal_id, m in metavars.items():
        if m.is_assigned:
            current = substitute_metavar(current, goal_id, m.assignment)
    return current


def instantiate(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """
    Recursively replace all assigned metavariables in an expression.
    """
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
    definitions: Definitions = None,
    unfolding: frozenset[str] = frozenset(),
) -> Expr:
    """
    Reduce an expression to weak head normal form.
    """
    expr = instantiate_metavar(expr, metavars)
    match expr:
        case EConst(name, _):
            if definitions is not None and name in definitions and definitions[name] is not None and name not in unfolding:
                return whnf(definitions[name], metavars, definitions, unfolding | {name})
            return expr
        case EApp(fn, arg):
            fn_whnf = whnf(fn, metavars, definitions, unfolding)
            if isinstance(fn_whnf, ELam):
                new_expr = substitute_expr_var(fn_whnf.body, fn_whnf.var, arg)
                return whnf(new_expr, metavars, definitions, unfolding)
            return EApp(fn_whnf, arg)
        case _:
            return expr
