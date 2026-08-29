"""
Tactic for replacing the current goal or a local hypothesis with a definitionally equal expression.
"""
from __future__ import annotations

from ..ast import Expr
from ..errors import KernelStateError, KernelValueError, TacticError
from ..kernel import ProofManager


def change(manager: ProofManager, expr: Expr, hypothesis_name: str | None = None) -> None:
    """
    Change the current goal, or the type of a named hypothesis, to a definitionally equal expression.
    """
    if manager.is_closed:
        raise TacticError("No active goals remain.")

    try:
        if hypothesis_name is None:
            manager.change_goal(expr)
        else:
            manager.change_hypothesis(hypothesis_name, expr)
    except (KernelStateError, KernelValueError) as e:
        raise TacticError(f"change failed during kernel verification: {e}") from e
