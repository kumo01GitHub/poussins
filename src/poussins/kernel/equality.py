"""Kernel-level equality checking functions for expressions."""
from __future__ import annotations

from ..ast import (
    EApp,
    EBVar,
    EConst,
    EFVar,
    ELam,
    ELet,
    EMetaVar,
    EPi,
    ESort,
    Expr,
)
from ..environment import Environment
from .eval import instantiate, whnf
from .proof_state import MetaVar
from .univ import is_def_eq_univ


def is_alpha_eq(
    t1: Expr,
    t2: Expr,
) -> bool:
    """Return True when two expressions are alpha-equivalent."""
    if type(t1) is not type(t2):
        return False

    match (t1, t2):
        case (EFVar(n1), EFVar(n2)):
            result = n1 == n2
        case (EBVar(i1), EBVar(i2)):
            result = i1 == i2
        case (ESort(l1), ESort(l2)):
            result = l1 == l2
        case (EConst(n1, lv1), EConst(n2, lv2)):
            result = n1 == n2 and lv1 == lv2
        case (EMetaVar(g1), EMetaVar(g2)):
            result = g1 == g2
        case (EPi(_, d1, b1), EPi(_, d2, b2)) | (ELam(_, d1, b1), ELam(_, d2, b2)):
            result = is_alpha_eq(d1, d2) and is_alpha_eq(b1, b2)
        case (ELet(_, t1, v1, b1), ELet(_, t2, v2, b2)):
            result = (
                is_alpha_eq(t1, t2)
                and is_alpha_eq(v1, v2)
                and is_alpha_eq(b1, b2)
            )
        case (EApp(f1, a1), EApp(f2, a2)):
            result = is_alpha_eq(f1, f2) and is_alpha_eq(a1, a2)
        case _:
            result = False

    return result


def _contains_outer_bvar(expr: Expr, depth: int = 0) -> bool:
    """Return True when the expression contains `EBVar(depth)`."""
    match expr:
        case EBVar(index):
            return index == depth
        case EApp(fn, arg):
            return _contains_outer_bvar(fn, depth) or _contains_outer_bvar(arg, depth)
        case ELam(_, domain, body) | EPi(_, domain, body):
            return (
                _contains_outer_bvar(domain, depth)
                or _contains_outer_bvar(body, depth + 1)
            )
        case ELet(_, var_type, value, body):
            return (
                _contains_outer_bvar(var_type, depth)
                or _contains_outer_bvar(value, depth)
                or _contains_outer_bvar(body, depth + 1)
            )
        case _:
            return False


def _eta_contract_lam(expr: ELam) -> Expr | None:
    """Return eta-contracted body when `expr` has shape `fun x => f x`."""
    if not isinstance(expr.body, EApp):
        return None
    if not isinstance(expr.body.arg, EBVar):
        return None
    if expr.body.arg.index != 0:
        return None
    if _contains_outer_bvar(expr.body.fn):
        return None
    return expr.body.fn


def _is_def_eq_eta_expanded_pair(
    t1_whnf: Expr,
    t2_whnf: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
) -> bool | None:
    """Try eta-contraction on one side and continue definal equality check."""
    if isinstance(t1_whnf, ELam) and isinstance(t2_whnf, EFVar):
        contracted = _eta_contract_lam(t1_whnf)
        if contracted is None:
            return False
        return is_def_eq(contracted, t2_whnf, context, metavars, env)

    if isinstance(t1_whnf, EFVar) and isinstance(t2_whnf, ELam):
        contracted = _eta_contract_lam(t2_whnf)
        if contracted is None:
            return False
        return is_def_eq(t1_whnf, contracted, context, metavars, env)

    return None


def _is_def_eq_same_shape(
    t1_whnf: Expr,
    t2_whnf: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
) -> bool:
    """Compare same-shaped expressions for definitional equality."""
    match (t1_whnf, t2_whnf):
        case (ESort(level1), ESort(level2)):
            return is_def_eq_univ(level1, level2)
        case (EConst(n1, lv1), EConst(n2, lv2)):
            if n1 != n2 or len(lv1) != len(lv2):
                return False
            return all(is_def_eq_univ(l1, l2) for l1, l2 in zip(lv1, lv2, strict=False))
        case (EApp(f1, a1), EApp(f2, a2)):
            return (
                is_def_eq(f1, f2, context, metavars, env)
                and is_def_eq(a1, a2, context, metavars, env)
            )
        case (EPi(_, d1, b1), EPi(_, d2, b2)) | (ELam(_, d1, b1), ELam(_, d2, b2)):
            domains_eq = is_def_eq(d1, d2, context, metavars, env)
            if not domains_eq:
                return False
            return is_def_eq(b1, b2, context, metavars, env)
        case (ELet(_, t1, v1, b1), ELet(_, t2, v2, b2)):
            return (
                is_def_eq(t1, t2, context, metavars, env)
                and is_def_eq(v1, v2, context, metavars, env)
                and is_def_eq(b1, b2, context, metavars, env)
            )
        case _:
            return False


def is_def_eq(
    t1: Expr,
    t2: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> bool:
    """Return True when two expressions are definitionally equal."""
    t1 = instantiate(t1, metavars)
    t2 = instantiate(t2, metavars)
    if is_alpha_eq(t1, t2):
        return True

    t1_whnf = whnf(t1, metavars, env)
    t2_whnf = whnf(t2, metavars, env)
    if (t1_whnf != t1 or t2_whnf != t2) and is_alpha_eq(t1_whnf, t2_whnf):
        return True

    eta_result = _is_def_eq_eta_expanded_pair(
        t1_whnf,
        t2_whnf,
        context,
        metavars,
        env,
    )
    if eta_result is not None:
        return eta_result

    if type(t1_whnf) is not type(t2_whnf):
        return False

    return _is_def_eq_same_shape(t1_whnf, t2_whnf, context, metavars, env)
