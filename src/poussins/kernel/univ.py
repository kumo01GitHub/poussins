"""
Kernel-level universe management functions for comparing and unifying universe levels.
"""
from __future__ import annotations

from ..ast import (
    Expr, ESort, EVar, EConst, EPi, ELam, EApp, EMatch, EMetaVar,
    UnivLevelZero, UnivLevelSucc, UnivLevelParam, UnivLevelIMax,
)


def is_universe_leq(level_left: object, level_right: object) -> bool:
    """
    Return True when the left universe level is below or equal to the right.
    """
    if level_left == level_right:
        return True

    match (level_left, level_right):
        case (UnivLevelZero(), UnivLevelSucc(_)):
            return True
        case (UnivLevelSucc(pred_left), UnivLevelSucc(pred_right)):
            return is_universe_leq(pred_left, pred_right)
        case (UnivLevelZero(), UnivLevelIMax(left, right)):
            return is_universe_leq(level_left, left) or is_universe_leq(level_left, right)
        case (UnivLevelSucc(_), UnivLevelIMax(left, right)):
            return is_universe_leq(level_left, left) or is_universe_leq(level_left, right)
        case _:
            return False


def unify_univ_levels(l1: object, l2: object, univ_subst: dict[str, object]) -> dict[str, object] | None:
    """
    Attempt to unify two universe levels, returning a substitution mapping if successful.
    """
    if isinstance(l1, UnivLevelParam) and l1.name in univ_subst:
        l1 = univ_subst[l1.name]
    if isinstance(l2, UnivLevelParam) and l2.name in univ_subst:
        l2 = univ_subst[l2.name]

    if l1 == l2:
        return univ_subst

    if isinstance(l1, UnivLevelParam):
        return univ_subst | {l1.name: l2}
    if isinstance(l2, UnivLevelParam):
        return univ_subst | {l2.name: l1}

    match (l1, l2):
        case (UnivLevelSucc(p1), UnivLevelSucc(p2)):
            return unify_univ_levels(p1, p2, univ_subst)
        case (UnivLevelIMax(a1, b1), UnivLevelIMax(a2, b2)):
            subst = unify_univ_levels(a1, a2, univ_subst)
            if subst is None:
                return None
            return unify_univ_levels(b1, b2, subst)
        case _:
            return None


def is_def_eq_univ(l1: object, l2: object) -> bool:
    """
    Return True when two universe levels are definitionally equal.
    """
    return unify_univ_levels(l1, l2, {}) is not None


def instantiate_univ_level(level: object, level_subst: dict[str, object]) -> object:
    """
    Recursively traverse a universe level and return a new level with UnivLevelParam replaced according to the substitution mapping.
    """
    if not level_subst:
        return level

    match level:
        case UnivLevelParam():
            return level_subst.get(level.name, level)
        case UnivLevelZero():
            return level
        case UnivLevelSucc(p):
            return UnivLevelSucc(instantiate_univ_level(p, level_subst))
        case UnivLevelIMax(left, right):
            return UnivLevelIMax(
                instantiate_univ_level(left, level_subst),
                instantiate_univ_level(right, level_subst)
            )
        case _:
            return level


def instantiate_univ(expr: Expr, level_subst: dict[str, object]) -> Expr:
    """
    Recursively traverse an expression (Expr) and return a new Expr with UnivLevelParam replaced in ESort and EConst.
    """
    if not level_subst:
        return expr

    match expr:
        case ESort(level):
            return ESort(instantiate_univ_level(level, level_subst))
        case EVar(_):
            return expr
        case EConst(name, levels):
            new_levels = tuple(instantiate_univ_level(level, level_subst) for level in levels)
            return EConst(name, new_levels)
        case EApp(fn, arg):
            return EApp(
                instantiate_univ(fn, level_subst),
                instantiate_univ(arg, level_subst)
            )
        case ELam(name, type_, body):
            return ELam(
                name,
                instantiate_univ(type_, level_subst),
                instantiate_univ(body, level_subst)
            )
        case EPi(name, type_, body):
            return EPi(
                name,
                instantiate_univ(type_, level_subst),
                instantiate_univ(body, level_subst)
            )
        case EMatch(_, _, _, _) | EMetaVar(_):
            return expr
        case _:
            raise NotImplementedError(f"instantiate_univ not implemented for {type(expr).__name__}")
