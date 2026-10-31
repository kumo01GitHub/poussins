"""AST operation utilities for expression traversal, substitution, and analysis."""
from __future__ import annotations

from collections.abc import Sequence

from .expr import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
)
from .universe import UnivLevel, UnivLevelIMax, UnivLevelMax, UnivLevelParam, UnivLevelSucc, UnivLevelZero


# ------------------------------------------------------------------
# Expression Builders
# ------------------------------------------------------------------
def univ_level(level: int | str | UnivLevel) -> UnivLevel:
    """Build a universe level."""
    if isinstance(level, int):
        if level < 0:
            raise ValueError("Universe level must be non-negative.")
        else:
            univ_level: UnivLevel = UnivLevelZero()
            for _ in range(level):
                univ_level = UnivLevelSucc(univ_level)
            return univ_level
    elif isinstance(level, str):
        return UnivLevelParam(level)
    else:
        return level

def univ_levels(levels: Sequence[int | str | UnivLevel]) -> tuple[UnivLevel, ...]:
    """Build a tuple of universe levels."""
    return tuple(univ_level(lv) for lv in levels)

def sort(level: int | str | UnivLevel) -> Expr:
    """Build a sort expression."""
    if isinstance(level, UnivLevel):
        return ESort(level=level)
    else:
        return ESort(level=univ_level(level))

def app(fn: Expr | str, *args: Expr | str) -> Expr:
    """Build a left-associated application chain from a head and arguments."""
    result = fn if isinstance(fn, Expr) else EVar(fn)
    for arg in args:
        result = EApp(
            fn=result,
            arg=arg if isinstance(arg, Expr) else EVar(arg)
        )
    return result

def lam(
    binders: Sequence[tuple[str, Expr | str]],
    body: Expr | str,
) -> Expr:
    """Build nested lambdas from binders, ending in body."""
    result = body if isinstance(body, Expr) else EVar(body)
    for var_name, domain in reversed(binders):
        result = ELam(var_name, domain if isinstance(domain, Expr) else EVar(domain), result)
    return result

def pi(
    binders: Sequence[tuple[str, Expr | str]],
    body: Expr | str,
) -> Expr:
    """Build nested Pi types from binders, ending in body."""
    result = body if isinstance(body, Expr) else EVar(body)
    for var_name, domain in reversed(binders):
        result = EPi(var_name, domain if isinstance(domain, Expr) else EVar(domain), result)
    return result

def decompose_app(expr: Expr) -> tuple[Expr, tuple[Expr, ...]]:
    """Decompose a left-associated application chain into its head and arguments."""
    head = expr
    args: list[Expr] = []
    while isinstance(head, EApp):
        args.append(head.arg)
        head = head.fn
    return head, tuple(reversed(args))


# ------------------------------------------------------------------
# Universe Utilities
# ------------------------------------------------------------------
def collect_univ_levels(expr: Expr) -> tuple[UnivLevel, ...]:
    """Collect all unique universe levels present in the expression."""
    ordered_levels: list[UnivLevel] = []

    def _collect(e: Expr) -> None:
        match e:
            case ESort(level):
                if level not in ordered_levels:
                    ordered_levels.append(level)
            case EConst(_, levels):
                for lvl in levels:
                    if lvl not in ordered_levels:
                        ordered_levels.append(lvl)
            case EVar(_) | EMetaVar(_):
                pass
            case EPi(_, domain, body) | ELam(_, domain, body):
                _collect(domain)
                _collect(body)
            case EApp(fn, arg):
                _collect(fn)
                _collect(arg)
            case EMatch(_, discriminee, motive, cases):
                _collect(discriminee)
                _collect(motive)
                for case_expr in cases:
                    _collect(case_expr)

    _collect(expr)

    return tuple(ordered_levels)

def collect_univ_level_params(expr: Expr, base: Sequence[str] | None = None) -> tuple[str, ...]:
    """Collect all unique universe level parameters present in the expression."""
    params: list[str] = list(base) if base is not None else []

    def _collect_from_univ_level(level: UnivLevel) -> None:
        match level:
            case UnivLevelParam(name):
                if name not in params:
                    params.append(name)
            case UnivLevelSucc(pred):
                _collect_from_univ_level(pred)
            case UnivLevelMax(left, right) | UnivLevelIMax(left, right):
                _collect_from_univ_level(left)
                _collect_from_univ_level(right)
            case _:
                pass

    def _collect_from_expr(e: Expr) -> None:
        match e:
            case ESort(level):
                _collect_from_univ_level(level)
            case EConst(_, levels):
                for lvl in levels:
                    _collect_from_univ_level(lvl)
            case EPi(_, domain, body) | ELam(_, domain, body):
                _collect_from_expr(domain)
                _collect_from_expr(body)
            case EApp(fn, arg):
                _collect_from_expr(fn)
                _collect_from_expr(arg)
            case EMatch(_, discriminee, motive, cases):
                _collect_from_expr(discriminee)
                _collect_from_expr(motive)
                for case_expr in cases:
                    _collect_from_expr(case_expr)
            case _:
                pass

    _collect_from_expr(expr)

    return tuple(params)

# ------------------------------------------------------------------
# Variable Utilities
# ------------------------------------------------------------------
def substitute_var(expr: Expr, var_name: str, replacement: Expr) -> Expr:
    """Substitute all occurrences of the variable."""
    replacement_fvs = collect_free_vars(replacement)

    def _subst(e: Expr) -> Expr:
        match e:
            case EVar(name):
                return replacement if name == var_name else e
            case ESort(_) | EConst(_) | EMetaVar(_):
                return e

            case EPi(var, domain, body):
                new_domain = _subst(domain)
                if var == var_name:
                    return EPi(var, new_domain, body)

                if var in replacement_fvs:
                    new_var = var + "_"
                    while new_var in replacement_fvs or new_var == var_name:
                        new_var += "_"
                    alpha_body = substitute_var(body, var, EVar(new_var))
                    return EPi(
                        new_var,
                        new_domain,
                        substitute_var(alpha_body, var_name, replacement)
                    )

                return EPi(var, new_domain, _subst(body))

            case ELam(var, domain, body):
                new_domain = _subst(domain)
                if var == var_name:
                    return ELam(var, new_domain, body)

                if var in replacement_fvs:
                    new_var = var + "_"
                    while new_var in replacement_fvs or new_var == var_name:
                        new_var += "_"
                    alpha_body = substitute_var(body, var, EVar(new_var))
                    return ELam(
                        new_var,
                        new_domain,
                        substitute_var(alpha_body, var_name, replacement)
                    )

                return ELam(var, new_domain, _subst(body))

            case EApp(fn, arg):
                return EApp(_subst(fn), _subst(arg))
            case EMatch(inductive_name, discriminee, motive, cases):
                return EMatch(
                    inductive_name,
                    _subst(discriminee),
                    _subst(motive),
                    tuple(_subst(c) for c in cases)
                )

    return _subst(expr)

def collect_free_vars(expr: Expr) -> set[str]:
    """Collect all free variable names present in the expression."""
    match expr:
        case EVar(name):
            return {name}
        case ESort(_) | EConst(_) | EMetaVar(_):
            return set()
        case EPi(var, domain, body) | ELam(var, domain, body):
            return collect_free_vars(domain) | (collect_free_vars(body) - {var})
        case EApp(fn, arg):
            return collect_free_vars(fn) | collect_free_vars(arg)
        case EMatch(_, discriminee, motive, cases):
            fvs = collect_free_vars(discriminee) | collect_free_vars(motive)
            for c in cases:
                fvs |= collect_free_vars(c)
            return fvs


# ------------------------------------------------------------------
# Meta-variable Utilities
# ------------------------------------------------------------------
def has_metavar(expr: Expr) -> bool:
    """Check if the expression contains any meta-variables (holes)."""
    match expr:
        case EMetaVar(_):
            return True
        case ESort(_) | EVar(_) | EConst(_):
            return False
        case EPi(_, domain, body) | ELam(_, domain, body):
            return has_metavar(domain) or has_metavar(body)
        case EApp(fn, arg):
            return has_metavar(fn) or has_metavar(arg)
        case EMatch(_, discriminee, motive, cases):
            return (
                has_metavar(discriminee)
                or has_metavar(motive)
                or any(has_metavar(c) for c in cases)
            )


def substitute_metavar(
    expr: Expr, target_goal_id: str, replacement: Expr | None
) -> Expr:
    """Substitute all occurrences of the meta-variable."""
    if replacement is None:
        raise ValueError("Replacement expression cannot be None.")

    match expr:
        case EMetaVar(goal_id):
            return replacement if goal_id == target_goal_id else expr
        case ESort(_) | EVar(_) | EConst(_):
            return expr
        case EPi(var, domain, body):
            return EPi(
                var,
                substitute_metavar(domain, target_goal_id, replacement),
                substitute_metavar(body, target_goal_id, replacement)
            )
        case ELam(var, domain, body):
            return ELam(
                var,
                substitute_metavar(domain, target_goal_id, replacement),
                substitute_metavar(body, target_goal_id, replacement)
            )
        case EApp(fn, arg):
            return EApp(
                substitute_metavar(fn, target_goal_id, replacement),
                substitute_metavar(arg, target_goal_id, replacement)
            )
        case EMatch(inductive_name, discriminee, motive, cases):
            return EMatch(
                inductive_name,
                substitute_metavar(discriminee, target_goal_id, replacement),
                substitute_metavar(motive, target_goal_id, replacement),
                tuple(substitute_metavar(c, target_goal_id, replacement) for c in cases)
            )

def collect_metavar_ids(expr: Expr) -> list[str]:
    """Collect all unique meta-variable goal IDs present in the expression."""
    ordered_ids: list[str] = []

    def _collect(e: Expr) -> None:
        match e:
            case EMetaVar(goal_id):
                if goal_id not in ordered_ids:
                    ordered_ids.append(goal_id)
            case ESort(_) | EVar(_) | EConst(_):
                pass
            case EPi(_, domain, body) | ELam(_, domain, body):
                _collect(domain)
                _collect(body)
            case EApp(fn, arg):
                _collect(fn)
                _collect(arg)
            case EMatch(_, discriminee, motive, cases):
                _collect(discriminee)
                _collect(motive)
                for case_expr in cases:
                    _collect(case_expr)

    _collect(expr)
    return ordered_ids


# ------------------------------------------------------------------
# Expression Utilities
# ------------------------------------------------------------------
def substitute_expr(expr: Expr, target: Expr, replacement: Expr) -> Expr:
    """Recursively replace all occurrences of `target` with `replacement` in `expr`."""
    if expr == target:
        return replacement

    match expr:
        case EApp(fn, arg):
            return EApp(
                substitute_expr(fn, target, replacement),
                substitute_expr(arg, target, replacement),
            )
        case ELam(var_name, var_type, body):
            return ELam(
                var_name,
                substitute_expr(var_type, target, replacement),
                substitute_expr(body, target, replacement),
            )
        case EPi(var_name, var_type, body):
            return EPi(
                var_name,
                substitute_expr(var_type, target, replacement),
                substitute_expr(body, target, replacement),
            )
        case EMatch(inductive_name, discriminee, motive, cases):
            return EMatch(
                inductive_name,
                substitute_expr(discriminee, target, replacement),
                substitute_expr(motive, target, replacement),
                tuple(substitute_expr(c, target, replacement) for c in cases),
            )
        case _:
            return expr

def count_pi_binders(expr: Expr) -> int:
    """Count the number of nested EPi binders (arity) in an expression."""
    count = 0
    current = expr
    while isinstance(current, EPi):
        count += 1
        current = current.body
    return count
