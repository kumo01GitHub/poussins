"""Kernel-level universe management functions."""
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
    UnivLevel,
    UnivLevelIMax,
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)


def flatten_univ_level_max(level: UnivLevel) -> set[UnivLevel]:
    """Recursively flatten a UnivLevelMax into a set of its constituent levels."""
    if isinstance(level, UnivLevelMax):
        return flatten_univ_level_max(level.left) | flatten_univ_level_max(level.right)
    else:
        return {level}


def is_universe_leq(level_left: UnivLevel, level_right: UnivLevel) -> bool:
    """Return True when the left universe level is below or equal to the right."""
    if (level_left == level_right) or isinstance(level_left, UnivLevelZero):
        return True

    if isinstance(level_left, UnivLevelMax):
        return all(
            is_universe_leq(level, level_right)
            for level in flatten_univ_level_max(level_left)
        )
    if isinstance(level_right, UnivLevelMax):
        return any(
            is_universe_leq(level_left, level)
            for level in flatten_univ_level_max(level_right)
        )

    match (level_left, level_right):
        case (UnivLevelSucc(pred_left), UnivLevelSucc(pred_right)):
            return is_universe_leq(pred_left, pred_right)
        case (_, UnivLevelSucc(pred_right)):
            return is_universe_leq(level_left, pred_right)
        case (UnivLevelIMax(left, right), _):
            return (
                is_universe_leq(right, UnivLevelZero())
                or (
                    is_universe_leq(left, level_right)
                    and is_universe_leq(right, level_right)
                )
            )
        case (_, UnivLevelIMax(left, right)):
            return (
                is_universe_leq(level_left, left)
                or is_universe_leq(level_left, right)
            )
        case _:
            return False


def unify_univ_levels(
    l1: UnivLevel, l2: UnivLevel,
    param_assignment: dict[str, UnivLevel]
) -> dict[str, UnivLevel] | None:
    """Attempt to unify two universe levels."""
    if isinstance(l1, UnivLevelParam) and l1.name in param_assignment:
        l1 = param_assignment[l1.name]
    if isinstance(l2, UnivLevelParam) and l2.name in param_assignment:
        l2 = param_assignment[l2.name]

    if l1 == l2:
        return param_assignment

    if isinstance(l1, UnivLevelParam):
        return param_assignment | {l1.name: l2}
    if isinstance(l2, UnivLevelParam):
        return param_assignment | {l2.name: l1}

    match (l1, l2):
        case (UnivLevelSucc(p1), UnivLevelSucc(p2)):
            return unify_univ_levels(p1, p2, param_assignment)
        case (UnivLevelIMax(a1, b1), UnivLevelIMax(a2, b2)):
            subst = unify_univ_levels(a1, a2, param_assignment)
            if subst is None:
                return None
            return unify_univ_levels(b1, b2, subst)
        case _:
            return None


def is_def_eq_univ(l1: UnivLevel, l2: UnivLevel) -> bool:
    """Return True when two universe levels are definitionally equal."""
    return unify_univ_levels(l1, l2, {}) is not None


def instantiate_univ_level(
    level: UnivLevel,
    param_assignment: dict[str, UnivLevel]
) -> UnivLevel:
    """Return a new UnivLevel with parameters replaced according to param_assignment."""
    if not param_assignment:
        return level

    match level:
        case UnivLevelParam():
            return param_assignment.get(level.name, level)
        case UnivLevelZero():
            return level
        case UnivLevelSucc(p):
            return UnivLevelSucc(instantiate_univ_level(p, param_assignment))
        case UnivLevelMax(left, right):
            return UnivLevelMax(
                instantiate_univ_level(left, param_assignment),
                instantiate_univ_level(right, param_assignment)
            )
        case UnivLevelIMax(left, right):
            return UnivLevelIMax(
                instantiate_univ_level(left, param_assignment),
                instantiate_univ_level(right, param_assignment)
            )


def instantiate_univ(expr: Expr, param_assignment: dict[str, UnivLevel]) -> Expr:
    """Traverse an expression and return a new Expr with UnivLevelParam replaced."""
    if not param_assignment:
        return expr

    match expr:
        case ESort(level):
            return ESort(instantiate_univ_level(level, param_assignment))
        case EVar(_):
            return expr
        case EConst(name, levels):
            new_levels = tuple(
                instantiate_univ_level(level, param_assignment) for level in levels
            )
            return EConst(name, new_levels)
        case EApp(fn, arg):
            return EApp(
                instantiate_univ(fn, param_assignment),
                instantiate_univ(arg, param_assignment)
            )
        case ELam(name, type_, body):
            return ELam(
                name,
                instantiate_univ(type_, param_assignment),
                instantiate_univ(body, param_assignment)
            )
        case EPi(name, type_, body):
            return EPi(
                name,
                instantiate_univ(type_, param_assignment),
                instantiate_univ(body, param_assignment)
            )
        case EMatch(_, _, _, _) | EMetaVar(_):
            return expr
        case _:
            raise NotImplementedError(
                f"instantiate_univ not implemented for {type(expr).__name__}"
            )
