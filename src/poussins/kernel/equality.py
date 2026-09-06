"""Kernel-level equality checking functions for expressions."""
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
    collect_free_vars,
    substitute_expr_var,
)
from ..environment import Environment
from .eval import instantiate, whnf
from .proof_state import MetaVar
from .univ import is_def_eq_univ


def _alpha_eq_bound_var(
    n1: str,
    n2: str,
    bvars1: list[str],
    bvars2: list[str],
) -> bool:
    """Compare possibly bound variables by de Bruijn-like binder positions."""
    if n1 in bvars1 or n2 in bvars2:
        try:
            return bvars1.index(n1) == bvars2.index(n2)
        except ValueError:
            return False
    return n1 == n2


def _alpha_eq_match_cases(
    c1: tuple[Expr, ...],
    c2: tuple[Expr, ...],
    bvars1: list[str],
    bvars2: list[str],
) -> bool:
    """Compare match branches under the same binder context."""
    if len(c1) != len(c2):
        return False
    return all(
        is_alpha_eq(b1, b2, bvars1, bvars2)
        for b1, b2 in zip(c1, c2, strict=False)
    )


def is_alpha_eq(
    t1: Expr,
    t2: Expr,
    bvars1: list[str] | None = None,
    bvars2: list[str] | None = None
) -> bool:
    """Return True when two expressions are alpha-equivalent."""
    if type(t1) is not type(t2):
        return False

    bvars1 = [] if bvars1 is None else bvars1
    bvars2 = [] if bvars2 is None else bvars2

    match (t1, t2):
        case (EVar(n1), EVar(n2)):
            result = _alpha_eq_bound_var(n1, n2, bvars1, bvars2)
        case (ESort(l1), ESort(l2)):
            result = l1 == l2
        case (EConst(n1, lv1), EConst(n2, lv2)):
            result = n1 == n2 and lv1 == lv2
        case (EMetaVar(g1), EMetaVar(g2)):
            result = g1 == g2
        case (EPi(v1, d1, b1), EPi(v2, d2, b2)) | (ELam(v1, d1, b1), ELam(v2, d2, b2)):
            result = is_alpha_eq(d1, d2, bvars1, bvars2) and is_alpha_eq(
                b1, b2, [v1] + bvars1, [v2] + bvars2
            )
        case (EApp(f1, a1), EApp(f2, a2)):
            result = (
                is_alpha_eq(f1, f2, bvars1, bvars2)
                and is_alpha_eq(a1, a2, bvars1, bvars2)
            )
        case (EMatch(i1, d1, m1, c1), EMatch(i2, d2, m2, c2)):
            result = (
                i1 != i2
                or not is_alpha_eq(d1, d2, bvars1, bvars2)
                or not is_alpha_eq(m1, m2, bvars1, bvars2)
            )
            if not result:
                result = _alpha_eq_match_cases(c1, c2, bvars1, bvars2)
            else:
                result = False
        case _:
            result = False

    return result


def _eta_contract_lam(expr: ELam) -> Expr | None:
    """Return eta-contracted body when `expr` has shape `fun x => f x`."""
    if not isinstance(expr.body, EApp):
        return None
    if not isinstance(expr.body.arg, EVar):
        return None
    if expr.body.arg.name != expr.var:
        return None
    if expr.body.arg.name in collect_free_vars(expr.body.fn):
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
    if isinstance(t1_whnf, ELam) and isinstance(t2_whnf, EVar):
        contracted = _eta_contract_lam(t1_whnf)
        if contracted is None:
            return False
        return is_def_eq(contracted, t2_whnf, context, metavars, env)

    if isinstance(t1_whnf, EVar) and isinstance(t2_whnf, ELam):
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
        case (EApp(f1, a1), EApp(f2, a2)):
            return (
                is_def_eq(f1, f2, context, metavars, env)
                and is_def_eq(a1, a2, context, metavars, env)
            )
        case (EPi(v1, d1, b1), EPi(v2, d2, b2)) | (ELam(v1, d1, b1), ELam(v2, d2, b2)):
            domains_eq = is_def_eq(d1, d2, context, metavars, env)
            if not domains_eq:
                return False
            b2_norm = b2
            if v1 != v2:
                b2_norm = substitute_expr_var(b2, var_name=v2, replacement=EVar(v1))
            return is_def_eq(b1, b2_norm, context | {v1: d1}, metavars, env)
        case (EMatch(i1, d1, m1, c1), EMatch(i2, d2, m2, c2)):
            if i1 != i2:
                return False
            if not is_def_eq(d1, d2, context, metavars, env):
                return False
            if not is_def_eq(m1, m2, context, metavars, env):
                return False
            if len(c1) != len(c2):
                return False
            return all(
                is_def_eq(b1, b2, context, metavars, env)
                for b1, b2 in zip(c1, c2, strict=False)
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
