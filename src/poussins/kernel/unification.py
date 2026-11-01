"""Kernel-level unification functions for the proof system."""
from __future__ import annotations

from ..ast import (
    EApp,
    EConst,
    ELam,
    EMetaVar,
    EPi,
    ESort,
    Expr,
    UnivLevel,
    collect_metavar_ids,
)
from ..environment import Environment
from ..errors import KernelTypeError
from .equality import is_alpha_eq
from .eval import instantiate, whnf
from .proof_state import MetaVar
from .univ import instantiate_univ, unify_univ_levels


def _assign_open_metavar(
    mvar_expr: Expr, replacement: Expr, metavars: dict[str, MetaVar]
) -> dict[str, MetaVar] | None:
    """Assign an open metavariable when possible and return updated assignments."""
    if not isinstance(mvar_expr, EMetaVar):
        return None

    mvar_id = mvar_expr.goal_id
    if mvar_id not in metavars or metavars[mvar_id].is_assigned:
        return None
    if mvar_id in collect_metavar_ids(replacement):
        raise KernelTypeError(
            f"Unification failed: occurs check failed for ?{mvar_id} in {replacement}"
        )
    return (
        metavars
        | {
            mvar_id: MetaVar(
                statement=metavars[mvar_id].statement,
                assignment=replacement,
            )
        }
    )


def unify(
    t1: Expr,
    t2: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> dict[str, MetaVar]:
    """Unify two expressions and return updated metavariable assignments."""
    t1 = instantiate(t1, metavars)
    t2 = instantiate(t2, metavars)
    if is_alpha_eq(t1, t2):
        return metavars

    assigned_metavars = _assign_open_metavar(t1, t2, metavars)
    if assigned_metavars is not None:
        return assigned_metavars
    assigned_metavars = _assign_open_metavar(t2, t1, metavars)
    if assigned_metavars is not None:
        return assigned_metavars

    t1_whnf = whnf(t1, metavars, env)
    t2_whnf = whnf(t2, metavars, env)

    if t1_whnf != t1 or t2_whnf != t2:
        if is_alpha_eq(t1_whnf, t2_whnf):
            return metavars
        if isinstance(t1_whnf, EMetaVar) or isinstance(t2_whnf, EMetaVar):
            return unify(t1_whnf, t2_whnf, context, metavars, env)

    if type(t1_whnf) is not type(t2_whnf):
        raise KernelTypeError(
            f"Unification failed: type mismatch between {t1_whnf} and {t2_whnf}"
        )

    match (t1_whnf, t2_whnf):
        case (ESort(l1), ESort(l2)):
            subst = unify_univ_levels(l1, l2, {})
            if subst is not None:
                return metavars
            raise KernelTypeError(
                f"Unification failed: universe level mismatch between {l1} and {l2}"
            )
        case (EConst(n1, lv1), EConst(n2, lv2)):
            if n1 != n2 or len(lv1) != len(lv2):
                raise KernelTypeError(
                    f"Unification failed: constant mismatch: {t1_whnf} vs {t2_whnf}"
                )
            param_assignment: dict[str, UnivLevel] = {}
            for l1, l2 in zip(lv1, lv2, strict=False):
                res = unify_univ_levels(l1, l2, param_assignment)
                if res is None:
                    raise KernelTypeError(
                        "Unification failed: universe level mismatch "
                        + f"between {l1} and {l2}"
                    )
                param_assignment = res

            if param_assignment:
                updated_metavars = {}
                for m_id, mvar in metavars.items():
                    new_stmt = instantiate_univ(mvar.statement, param_assignment)
                    new_assignment = (
                        instantiate_univ(mvar.assignment, param_assignment)
                        if mvar.assignment is not None
                        else None
                    )
                    updated_metavars[m_id] = MetaVar(
                        statement=new_stmt, assignment=new_assignment
                    )
                return updated_metavars
            return metavars
        case (EApp(f1, a1), EApp(f2, a2)):
            current_metavars = unify(f1, f2, context, metavars, env)
            a1_inst = instantiate(a1, current_metavars)
            a2_inst = instantiate(a2, current_metavars)
            return unify(a1_inst, a2_inst, context, current_metavars, env)
        case (EPi(_, d1, b1), EPi(_, d2, b2)) | (ELam(_, d1, b1), ELam(_, d2, b2)):
            current_metavars = unify(d1, d2, context, metavars, env)
            b1_inst = instantiate(b1, current_metavars)
            b2_inst = instantiate(b2, current_metavars)
            return unify(
                b1_inst,
                b2_inst,
                context,
                current_metavars,
                env,
            )
        case _:
            raise KernelTypeError(
                "Unification failed: expressions are structurally distinct: "
                + f"{t1_whnf} vs {t2_whnf}"
            )
