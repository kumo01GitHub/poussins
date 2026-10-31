"""Shared helpers for tactic implementations."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Concatenate

from ..ast import EConst, Expr, count_pi_binders, decompose_app
from ..environment.library import EQ_IND_SPEC
from ..errors import TacticError
from ..kernel import Goal, ProofManager


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


def const_head_name(expr: Expr) -> str | None:
    """Return the head constant name of an application chain, if any."""
    head, _ = decompose_app(expr)
    if not isinstance(head, EConst):
        return None
    return head.name


def parse_eq_app(expr: Expr) -> tuple[Expr, Expr, Expr] | None:
    """Decode `Eq A lhs rhs` when the expression has that shape."""
    head, args = decompose_app(expr)
    if not isinstance(head, EConst):
        return None
    if (
        head.name != EQ_IND_SPEC.name
        or len(args) != count_pi_binders(
            EQ_IND_SPEC.type
        )
    ):
        return None
    return args[0], args[1], args[2]
