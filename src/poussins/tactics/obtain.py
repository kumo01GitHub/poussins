"""Introduce a hypothesis by destructing a proof term according to a pattern."""
from __future__ import annotations

from ..ast import EVar, Expr
from ..kernel import ProofManager, infer_type
from .cases import RCasesPattern, rcases
from .exact import exact
from .have import have
from .helpers import (
    fresh_binder_name,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def obtain(
    manager: ProofManager,
    pattern: RCasesPattern,
    expr: Expr,
) -> None:
    """Introduce a hypothesis by destructing a proof term according to a pattern."""
    if isinstance(expr, EVar):
        rcases(manager, hyp_name=expr.name, pattern=pattern)
        return

    current_goal = require_current_goal(manager)

    name = fresh_binder_name(
        "_obtain",
        current_goal.context,
        set(current_goal.local_context.keys()),
    )
    inferred_type = infer_type(
        expr,
        context=current_goal.context,
        metavars=manager.current_state.metavars,
        env=manager.env,
    )

    have(manager, name=name, expr=inferred_type)
    exact(manager, expr)
    rcases(manager, hyp_name=name, pattern=pattern)
