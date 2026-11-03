"""AST operation utilities for expression traversal, substitution, and analysis."""
from __future__ import annotations

from collections.abc import Sequence

from .expr import (
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
from .universe import (
    UnivLevel,
    UnivLevelIMax,
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)


# ------------------------------------------------------------------
# Expression Builders
# ------------------------------------------------------------------
def _abstract_name_to_bvar(expr: Expr, name: str) -> Expr:
    """Abstract free-variable `name` to the nearest de Bruijn index."""
    def _go(e: Expr, depth: int) -> Expr:
        match e:
            case EFVar(n):
                return EBVar(depth) if n == name else e
            case EApp(fn, arg):
                return EApp(_go(fn, depth), _go(arg, depth))
            case ELam(var, domain, body):
                return ELam(var, _go(domain, depth), _go(body, depth + 1))
            case ELet(var, var_type, value, body):
                return ELet(
                    var,
                    _go(var_type, depth),
                    _go(value, depth),
                    _go(body, depth + 1),
                )
            case EPi(var, domain, body):
                return EPi(var, _go(domain, depth), _go(body, depth + 1))
            case ESort() | EConst() | EBVar() | EMetaVar():
                return e

    return _go(expr, 0)


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
    result = fn if isinstance(fn, Expr) else EFVar(fn)
    for arg in args:
        result = EApp(
            fn=result,
            arg=arg if isinstance(arg, Expr) else EFVar(arg)
        )
    return result

def lam(
    binders: Sequence[tuple[str, Expr | str]],
    body: Expr | str,
) -> Expr:
    """Build nested lambdas from binders, ending in body."""
    result = body if isinstance(body, Expr) else EFVar(body)
    for var_name, domain in reversed(binders):
        dom = domain if isinstance(domain, Expr) else EFVar(domain)
        abstracted = (
            _abstract_name_to_bvar(result, var_name)
            if var_name != "_" else result
        )
        result = ELam(var_name, dom, abstracted)
    return result


def let_(
    var_name: str,
    var_type: Expr | str,
    value: Expr | str,
    body: Expr | str,
) -> Expr:
    """Build a let-binding expression with a single variable."""
    var_type_expr = var_type if isinstance(var_type, Expr) else EFVar(var_type)
    value_expr = value if isinstance(value, Expr) else EFVar(value)
    result = body if isinstance(body, Expr) else EFVar(body)
    abstracted = (
        _abstract_name_to_bvar(result, var_name)
        if var_name != "_" else result
    )
    return ELet(var_name, var_type_expr, value_expr, abstracted)


def pi(
    binders: Sequence[tuple[str, Expr | str]],
    body: Expr | str,
) -> Expr:
    """Build nested Pi types from binders, ending in body."""
    result = body if isinstance(body, Expr) else EFVar(body)
    for var_name, domain in reversed(binders):
        dom = domain if isinstance(domain, Expr) else EFVar(domain)
        abstracted = (
            _abstract_name_to_bvar(result, var_name)
            if var_name != "_" else result
        )
        result = EPi(var_name, dom, abstracted)
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
def collect_univ_level_params(
    expr: Expr,
    base: Sequence[str] | None = None
) -> tuple[str, ...]:
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
            case ELet(_, var_type, value, body):
                _collect_from_expr(var_type)
                _collect_from_expr(value)
                _collect_from_expr(body)
            case EApp(fn, arg):
                _collect_from_expr(fn)
                _collect_from_expr(arg)
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
            case EFVar(name):
                return replacement if name == var_name else e
            case ESort(_) | EConst(_) | EBVar(_) | EMetaVar(_):
                return e

            case EPi(var, domain, body):
                new_domain = _subst(domain)
                if var == var_name:
                    return EPi(var, new_domain, body)

                if var in replacement_fvs:
                    new_var = var + "_"
                    while new_var in replacement_fvs or new_var == var_name:
                        new_var += "_"
                    alpha_body = substitute_var(body, var, EFVar(new_var))
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
                    alpha_body = substitute_var(body, var, EFVar(new_var))
                    return ELam(
                        new_var,
                        new_domain,
                        substitute_var(alpha_body, var_name, replacement)
                    )

                return ELam(var, new_domain, _subst(body))

            case ELet(var, var_type, value, body):
                new_var_type = _subst(var_type)
                new_value = _subst(value)
                if var == var_name:
                    return ELet(var, new_var_type, new_value, body)

                if var in replacement_fvs:
                    new_var = var + "_"
                    while new_var in replacement_fvs or new_var == var_name:
                        new_var += "_"
                    alpha_body = substitute_var(body, var, EFVar(new_var))
                    return ELet(
                        new_var,
                        new_var_type,
                        new_value,
                        substitute_var(alpha_body, var_name, replacement)
                    )

                return ELet(var, new_var_type, new_value, _subst(body))

            case EApp(fn, arg):
                return EApp(_subst(fn), _subst(arg))

    return _subst(expr)

def collect_free_vars(expr: Expr) -> set[str]:
    """Collect all free variable names present in the expression."""
    match expr:
        case EFVar(name):
            return {name}
        case ESort(_) | EConst(_) | EBVar(_) | EMetaVar(_):
            return set()
        case EPi(var, domain, body) | ELam(var, domain, body):
            return collect_free_vars(domain) | (collect_free_vars(body) - {var})
        case ELet(var, var_type, value, body):
            return (
                collect_free_vars(var_type)
                | collect_free_vars(value)
                | (collect_free_vars(body) - {var})
            )
        case EApp(fn, arg):
            return collect_free_vars(fn) | collect_free_vars(arg)


# ------------------------------------------------------------------
# Meta-variable Utilities
# ------------------------------------------------------------------
def has_metavar(expr: Expr) -> bool:
    """Check if the expression contains any meta-variables (holes)."""
    match expr:
        case EMetaVar(_):
            return True
        case ESort(_) | EFVar(_) | EBVar(_) | EConst(_):
            return False
        case EPi(_, domain, body) | ELam(_, domain, body):
            return has_metavar(domain) or has_metavar(body)
        case ELet(_, var_type, value, body):
            return (
                has_metavar(var_type)
                or has_metavar(value)
                or has_metavar(body)
            )
        case EApp(fn, arg):
            return has_metavar(fn) or has_metavar(arg)


def substitute_metavar(
    expr: Expr, target_goal_id: str, replacement: Expr | None
) -> Expr:
    """Substitute all occurrences of the meta-variable."""
    if replacement is None:
        raise ValueError("Replacement expression cannot be None.")

    match expr:
        case EMetaVar(goal_id):
            return replacement if goal_id == target_goal_id else expr
        case ESort(_) | EFVar(_) | EBVar(_) | EConst(_):
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
        case ELet(var, var_type, value, body):
            return ELet(
                var,
                substitute_metavar(var_type, target_goal_id, replacement),
                substitute_metavar(value, target_goal_id, replacement),
                substitute_metavar(body, target_goal_id, replacement)
            )
        case EApp(fn, arg):
            return EApp(
                substitute_metavar(fn, target_goal_id, replacement),
                substitute_metavar(arg, target_goal_id, replacement)
            )

def collect_metavar_ids(expr: Expr) -> list[str]:
    """Collect all unique meta-variable goal IDs present in the expression."""
    ordered_ids: list[str] = []

    def _collect(e: Expr) -> None:
        match e:
            case EMetaVar(goal_id):
                if goal_id not in ordered_ids:
                    ordered_ids.append(goal_id)
            case ESort(_) | EFVar(_) | EBVar(_) | EConst(_):
                pass
            case EPi(_, domain, body) | ELam(_, domain, body):
                _collect(domain)
                _collect(body)
            case ELet(_, var_type, value, body):
                _collect(var_type)
                _collect(value)
                _collect(body)
            case EApp(fn, arg):
                _collect(fn)
                _collect(arg)

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
        case ELet(var_name, var_type, value, body):
            return ELet(
                var_name,
                substitute_expr(var_type, target, replacement),
                substitute_expr(value, target, replacement),
                substitute_expr(body, target, replacement),
            )
        case EPi(var_name, var_type, body):
            return EPi(
                var_name,
                substitute_expr(var_type, target, replacement),
                substitute_expr(body, target, replacement),
            )
        case _:
            return expr


def shift_bvars(expr: Expr, delta: int, cutoff: int = 0) -> Expr:
    """Shift de Bruijn indices by delta at or above cutoff."""
    def _shift(e: Expr, depth: int) -> Expr:
        match e:
            case EBVar(index):
                if index >= cutoff + depth:
                    return EBVar(index + delta)
                return e
            case EApp(fn, arg):
                return EApp(_shift(fn, depth), _shift(arg, depth))
            case ELam(var, domain, body):
                return ELam(var, _shift(domain, depth), _shift(body, depth + 1))
            case ELet(var, var_type, value, body):
                return ELet(
                    var,
                    _shift(var_type, depth),
                    _shift(value, depth),
                    _shift(body, depth + 1),
                )
            case EPi(var, domain, body):
                return EPi(var, _shift(domain, depth), _shift(body, depth + 1))
            case _:
                return e

    return _shift(expr, 0)


def substitute_bvar(expr: Expr, index: int, replacement: Expr) -> Expr:
    """Substitute a de Bruijn variable at index with replacement."""
    def _subst(e: Expr, depth: int) -> Expr:
        match e:
            case EBVar(i):
                if i == index + depth:
                    return shift_bvars(replacement, depth)
                return e
            case EApp(fn, arg):
                return EApp(_subst(fn, depth), _subst(arg, depth))
            case ELam(var, domain, body):
                return ELam(var, _subst(domain, depth), _subst(body, depth + 1))
            case ELet(var, var_type, value, body):
                return ELet(
                    var,
                    _subst(var_type, depth),
                    _subst(value, depth),
                    _subst(body, depth + 1),
                )
            case EPi(var, domain, body):
                return EPi(var, _subst(domain, depth), _subst(body, depth + 1))
            case _:
                return e

    return _subst(expr, 0)


def substitute_bvar_top(expr: Expr, replacement: Expr) -> Expr:
    """Substitute the nearest bound variable (#0) and close one binder."""
    return shift_bvars(substitute_bvar(expr, 0, shift_bvars(replacement, 1)), -1)


def instantiate_binder(expr: Expr, replacement: Expr) -> Expr:
    """Instantiate one de Bruijn binder body with a replacement expression."""
    return substitute_bvar_top(expr, replacement)

def count_pi_binders(expr: Expr) -> int:
    """Count the number of nested EPi binders (arity) in an expression."""
    count = 0
    current = expr
    while isinstance(current, EPi):
        count += 1
        current = current.body
    return count
