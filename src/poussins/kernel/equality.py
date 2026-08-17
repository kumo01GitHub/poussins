"""
Kernel-level equality checking functions for expressions, including alpha-equivalence and definitional equality.
"""
from __future__ import annotations

from .eval import instantiate, whnf
from .proof_state import MetaVar
from .univ import is_def_eq_univ
from ..ast import (
    Expr, ESort, EVar, EConst, EApp, ELam, EPi, EMatch, EMetaVar,
    collect_free_vars, substitute_expr_var
)
from ..environment import Environment


def is_alpha_eq(t1: Expr, t2: Expr, bvars1: list[str] = [], bvars2: list[str] = []) -> bool:
    """
    Return True when two expressions are alpha-equivalent.
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


def is_def_eq(
    t1: Expr,
    t2: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> bool:
    """
    Return True when two expressions are definitionally equal.
    """
    t1 = instantiate(t1, metavars)
    t2 = instantiate(t2, metavars)
    if is_alpha_eq(t1, t2):
        return True

    t1_whnf = whnf(t1, metavars, env)
    t2_whnf = whnf(t2, metavars, env)
    if t1_whnf != t1 or t2_whnf != t2:
        if is_alpha_eq(t1_whnf, t2_whnf):
            return True
        if isinstance(t1_whnf, ELam) and isinstance(t2_whnf, EVar):
            if not isinstance(t1_whnf.body, EApp):
                return False
            if not isinstance(t1_whnf.body.arg, EVar):
                return False
            if t1_whnf.body.arg.name != t1_whnf.var:
                return False
            if t1_whnf.body.arg.name in collect_free_vars(t1_whnf.body.fn):
                return False
            return is_def_eq(t1_whnf.body.fn, t2_whnf, context, metavars, env)

        if isinstance(t1_whnf, EVar) and isinstance(t2_whnf, ELam):
            if not isinstance(t2_whnf.body, EApp):
                return False
            if not isinstance(t2_whnf.body.arg, EVar):
                return False
            if t2_whnf.body.arg.name != t2_whnf.var:
                return False
            if t2_whnf.body.arg.name in collect_free_vars(t2_whnf.body.fn):
                return False
            return is_def_eq(t1_whnf, t2_whnf.body.fn, context, metavars, env)

    if type(t1_whnf) is not type(t2_whnf):
        return False

    match (t1_whnf, t2_whnf):
        case (ESort(level1), ESort(level2)):
            return is_def_eq_univ(level1, level2)
        case (EApp(f1, a1), EApp(f2, a2)):
            return (
                is_def_eq(f1, f2, context, metavars, env) and
                is_def_eq(a1, a2, context, metavars, env)
            )
        case (EPi(v1, d1, b1), EPi(v2, d2, b2)) | (ELam(v1, d1, b1), ELam(v2, d2, b2)):
            if not is_def_eq(d1, d2, context, metavars, env):
                return False
            if v1 != v2:
                b2 = substitute_expr_var(b2, var_name=v2, replacement=EVar(v1))
            return is_def_eq(b1, b2, context | {v1: d1}, metavars, env)
        case (EMatch(i1, d1, m1, c1), EMatch(i2, d2, m2, c2)):
            if i1 != i2:
                return False
            if not is_def_eq(d1, d2, context, metavars, env):
                return False
            if not is_def_eq(m1, m2, context, metavars, env):
                return False
            if len(c1) != len(c2):
                return False
            return all(is_def_eq(b1, b2, context, metavars, env) for b1, b2 in zip(c1, c2))
        case _:
            return False
