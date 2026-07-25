"""
Kernel-level expression type inference and checking (Dependent Type Theory).
This module is COMPLETELY STATELESS and has ZERO dependency on Environment or Framework.
"""
from __future__ import annotations

from .proof_state import MetaVar
from ..ast import (
    Expr, ESort, EVar, EConst, EPi, ELam, EApp, EMatch, EMetaVar,
    UnivLevelSucc, UnivLevelIMax,
    substitute_meta_var, substitute_expr_var
)
from ..errors import KernelTypeError


def instantiate_meta(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """
    Instantiate meta-variables in the expression based on the given metavars dictionary.
    """
    current = expr
    for goal_id, m in metavars.items():
        if m.is_assigned:
            current = substitute_meta_var(current, goal_id, m.assignment)
    return current


def whnf(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """
    Weak Head Normal Form (WHNF) evaluation of the expression.
    """
    expr = instantiate_meta(expr, metavars)

    match expr:
        case EApp(fn, arg):
            fn_whnf = whnf(fn, metavars)
            if isinstance(fn_whnf, ELam):
                new_expr = substitute_expr_var(fn_whnf.body, fn_whnf.var, arg)
                return whnf(new_expr, metavars)
            else:
                return EApp(fn_whnf, arg)
        case _:
            return expr


def instantiate(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """
    Fully instantiate the expression by recursively replacing all meta-variables with their assignments.
    """
    current = expr
    while True:
        next_term = instantiate_meta(current, metavars)
        if next_term == current:
            break
        current = next_term
    return current


def infer_type(expr: Expr, context: dict[str, Expr], metavars: dict[str, MetaVar]) -> Expr:
    """Infer the type (which is also an Expr) of the given expression."""
    expr = instantiate_meta(expr, metavars)

    match expr:
        case EMetaVar(goal_id):
            if goal_id not in metavars:
                raise KernelTypeError(f"Unknown meta-variable ?{goal_id}")
            return metavars[goal_id].statement

        case ESort(level):
            return ESort(UnivLevelSucc(level))

        case EVar(name) | EConst(name, _):
            t = context.get(name)
            if t is None:
                raise KernelTypeError(f"Unknown identifier '{name}' (neither local variable nor verified constant).")
            return t

        case EPi(var, domain, body):
            sort_a = infer_type(domain, context, metavars)
            sort_a_whnf = whnf(sort_a, metavars)
            if not isinstance(sort_a_whnf, ESort):
                raise KernelTypeError("The domain of a dependent product must be a Sort.")

            sort_b = infer_type(body, context | {var: domain}, metavars)
            sort_b_whnf = whnf(sort_b, metavars)
            if not isinstance(sort_b_whnf, ESort):
                raise KernelTypeError("The body of a dependent product must be a Sort.")

            return ESort(UnivLevelIMax(sort_a_whnf.level, sort_b_whnf.level))

        case ELam(var, domain, body):
            extended_context = context | {var: domain}
            body_type = infer_type(body, extended_context, metavars)

            infer_type(EPi(var, domain, body_type), context, metavars)
            return EPi(var, domain, body_type)

        case EApp(fn, arg):
            fn_type = infer_type(fn, context, metavars)
            arg_type = infer_type(arg, context, metavars)

            fn_type_whnf = whnf(fn_type, metavars)

            if not isinstance(fn_type_whnf, EPi):
                raise KernelTypeError(f"Expected function type (EPi), but found: {fn_type_whnf}")

            expected_domain = whnf(fn_type_whnf.domain, metavars)
            actual_arg_type = whnf(arg_type, metavars)
            if expected_domain != actual_arg_type:
                raise KernelTypeError(f"Argument type mismatch. Expected: {expected_domain}, Found: {actual_arg_type}")

            return substitute_expr_var(fn_type_whnf.body, fn_type_whnf.var, arg)

        case EMatch(_, discriminee, motive, _):
            return EApp(motive, discriminee)

        case _:
            raise NotImplementedError(f"Unknown expression node: {expr}")


def check_type(expr: Expr, expected_type: Expr, context: dict[str, Expr], metavars: dict[str, MetaVar]) -> bool:
    """Return True when the expression checks against the expected type in the given context."""
    try:
        inferred = infer_type(expr, context, metavars)
        return whnf(inferred, metavars) == whnf(expected_type, metavars)
    except KernelTypeError:
        return False


def is_alpha_eq(t1: Expr, t2: Expr, bvars1: list[str] = [], bvars2: list[str] = []) -> bool:
    """
    Check if two expressions are alpha-equivalent, considering bound variable names.
    """
    if type(t1) is not type(t2):
        return False

    match (t1, t2):
        case (EVar(n1), EVar(n2)):
            if n1 in bvars1 or n2 in bvars2:
                try:
                    return bvars1.index(n1) == bvars2.index(n2)
                except ValueError:
                    return False
            return n1 == n2

        case (ESort(l1), ESort(l2)):
            return l1 == l2

        case (EConst(n1, lv1), EConst(n2, lv2)):
            return n1 == n2 and lv1 == lv2

        case (EMetaVar(g1), EMetaVar(g2)):
            return g1 == g2

        case (EPi(v1, d1, b1), EPi(v2, d2, b2)) | (ELam(v1, d1, b1), ELam(v2, d2, b2)):
            if not is_alpha_eq(d1, d2, bvars1, bvars2):
                return False
            return is_alpha_eq(b1, b2, [v1] + bvars1, [v2] + bvars2)

        case (EApp(f1, a1), EApp(f2, a2)):
            return is_alpha_eq(f1, f2, bvars1, bvars2) and is_alpha_eq(a1, a2, bvars1, bvars2)

        case (EMatch(i1, d1, m1, c1), EMatch(i2, d2, m2, c2)):
            if i1 != i2 or not is_alpha_eq(d1, d2, bvars1, bvars2) or not is_alpha_eq(m1, m2, bvars1, bvars2):
                return False
            if len(c1) != len(c2):
                return False
            return all(is_alpha_eq(b1, b2, bvars1, bvars2) for b1, b2 in zip(c1, c2))

        case _:
            return False
