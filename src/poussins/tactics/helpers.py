"""Shared helpers for tactic implementations."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar

from ..ast import EApp, EConst, ELam, Expr
from ..errors import TacticError
from ..kernel import Goal, ProofManager

_EQ_APP_ARITY = 3
_P = ParamSpec("_P")
_R = TypeVar("_R")


def require_current_goal(
    manager: ProofManager,
    *,
    tactic_name: str | None = None,
) -> Goal:
    """Return the current goal, or raise a tactic error when none is active."""
    msg = "No active goals remain."
    if tactic_name is not None:
        msg = f"{tactic_name} failed: No active goals remain."

    if manager.is_closed:
        raise TacticError(msg)

    current_goal = manager.current_state.current_goal
    if current_goal is None:
        raise TacticError(msg)

    return current_goal


def requires_active_goal[**P, R](
    func: Callable[Concatenate[ProofManager, P], R],
) -> Callable[Concatenate[ProofManager, P], R]:
    """Require that the tactic has an active goal before executing the function."""

    @wraps(func)
    def wrapper(manager: ProofManager, *args: P.args, **kwargs: P.kwargs) -> R:
        require_current_goal(manager, tactic_name=func.__name__)
        return func(manager, *args, **kwargs)

    return wrapper


def fresh_binder_name(
    base: str, context: dict[str, Expr], used_names: set[str]
) -> str:
    """Produce a fresh binder name that does not collide with context."""
    candidate = base
    counter = 0
    while candidate in context or candidate in used_names:
        counter += 1
        candidate = f"{base}{counter}"
    return candidate


def build_app(fn: Expr, *args: Expr) -> Expr:
    """Build a left-associated application chain."""
    result = fn
    for arg in args:
        result = EApp(result, arg)
    return result


def build_lambda_chain(
    binders: list[tuple[str, Expr]],
    body: Expr,
) -> Expr:
    """Build nested lambdas from binders, ending in body."""
    result = body
    for var_name, domain in reversed(binders):
        result = ELam(var_name, domain, result)
    return result


def flatten_app_chain(expr: Expr) -> tuple[Expr, tuple[Expr, ...]]:
    """Return the function head and its left-associated arguments."""
    head = expr
    args: list[Expr] = []
    while isinstance(head, EApp):
        args.append(head.arg)
        head = head.fn
    return head, tuple(reversed(args))


def const_head_name(expr: Expr) -> str | None:
    """Return the head constant name of an application chain, if any."""
    head, _ = flatten_app_chain(expr)
    if not isinstance(head, EConst):
        return None
    return head.name


def match_const_app(expr: Expr, const_name: str, arity: int) -> tuple[Expr, ...] | None:
    """Match a fully applied constant with a known arity."""
    head, args = flatten_app_chain(expr)
    if not isinstance(head, EConst):
        return None
    if head.name != const_name or len(args) != arity:
        return None
    return args


def split_eq_app(expr: Expr, eq_name: str = "Eq") -> tuple[Expr, Expr, Expr] | None:
    """Decode `Eq A lhs rhs` when the expression has that shape."""
    args = match_const_app(expr, eq_name, _EQ_APP_ARITY)
    if args is None:
        return None
    return args[0], args[1], args[2]
