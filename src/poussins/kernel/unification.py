"""
Kernel-level unification functions for the proof system.
"""
from __future__ import annotations

from .equality import is_alpha_eq
from .eval import instantiate, whnf
from .proof_state import MetaVar
from .univ import unify_univ_levels
from ..ast import (
    Expr, ESort, EVar, EPi, ELam, EApp, EMatch, EMetaVar,
    substitute_expr_var, collect_metavar_ids
)
from ..environment import Environment
from ..errors import KernelTypeError


def unify(
    t1: Expr,
    t2: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> dict[str, MetaVar]:
    """
    Unify two expressions and return updated metavariable assignments, with robust substitution propagation and occurs-check.
    """
    t1 = instantiate(t1, metavars)
    t2 = instantiate(t2, metavars)
    if is_alpha_eq(t1, t2):
        return metavars

    if isinstance(t1, EMetaVar):
        mvar_id = t1.goal_id
        if mvar_id in metavars and not metavars[mvar_id].is_assigned:
            if mvar_id in collect_metavar_ids(t2):
                raise KernelTypeError(f"Unification failed: occurs check failed for ?{mvar_id} in {t2}")
            return metavars | {mvar_id: MetaVar(statement=metavars[mvar_id].statement, assignment=t2)}
    if isinstance(t2, EMetaVar):
        mvar_id = t2.goal_id
        if mvar_id in metavars and not metavars[mvar_id].is_assigned:
            if mvar_id in collect_metavar_ids(t1):
                raise KernelTypeError(f"Unification failed: occurs check failed for ?{mvar_id} in {t1}")
            return metavars | {mvar_id: MetaVar(statement=metavars[mvar_id].statement, assignment=t1)}

    t1_whnf = whnf(t1, metavars, env)
    t2_whnf = whnf(t2, metavars, env)

    if t1_whnf != t1 or t2_whnf != t2:
        if is_alpha_eq(t1_whnf, t2_whnf):
            return metavars
        if isinstance(t1_whnf, EMetaVar) or isinstance(t2_whnf, EMetaVar):
            return unify(t1_whnf, t2_whnf, context, metavars, env)

    if type(t1_whnf) is not type(t2_whnf):
        raise KernelTypeError(f"Unification failed: type mismatch between {t1_whnf} and {t2_whnf}")

    match (t1_whnf, t2_whnf):
        case (ESort(l1), ESort(l2)):
            subst = unify_univ_levels(l1, l2, {})
            if subst is not None:
                return metavars
            raise KernelTypeError(f"Unification failed: universe level mismatch between {l1} and {l2}")
        case (EApp(f1, a1), EApp(f2, a2)):
            current_metavars = unify(f1, f2, context, metavars, env)
            a1_inst = instantiate(a1, current_metavars)
            a2_inst = instantiate(a2, current_metavars)
            return unify(a1_inst, a2_inst, context, current_metavars, env)
        case (EPi(v1, d1, b1), EPi(v2, d2, b2)) | (ELam(v1, d1, b1), ELam(v2, d2, b2)):
            current_metavars = unify(d1, d2, context, metavars, env)
            d1_inst = instantiate(d1, current_metavars)
            b1_inst = instantiate(b1, current_metavars)
            b2_inst = instantiate(b2, current_metavars)
            if v1 != v2:
                b2_inst = substitute_expr_var(b2_inst, var_name=v2, replacement=EVar(v1))
            return unify(b1_inst, b2_inst, context | {v1: d1_inst}, current_metavars, env)
        case (EMatch(i1, d1, m1, c1), EMatch(i2, d2, m2, c2)):
            if i1 != i2:
                raise KernelTypeError("Unification failed: match inductive type mismatch")
            current_metavars = unify(d1, d2, context, metavars, env)
            m1_inst = instantiate(m1, current_metavars)
            m2_inst = instantiate(m2, current_metavars)
            current_metavars = unify(m1_inst, m2_inst, context, current_metavars, env)
            if len(c1) != len(c2):
                raise KernelTypeError("Unification failed: match branch length mismatch")
            for b1, b2 in zip(c1, c2):
                b1_inst = instantiate(b1, current_metavars)
                b2_inst = instantiate(b2, current_metavars)
                current_metavars = unify(b1_inst, b2_inst, context, current_metavars, env)
            return current_metavars
        case _:
            raise KernelTypeError(f"Unification failed: expressions are structurally distinct: {t1_whnf} vs {t2_whnf}")
