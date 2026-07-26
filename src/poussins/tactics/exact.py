from __future__ import annotations

from ..ast import Expr
from ..errors import TacticError
from ..kernel import ProofManager


def exact(manager: ProofManager, expr: Expr) -> None:
    """
    Exact tactic: Close the current goal using the original expression.
    """
    if manager.is_closed:
        raise TacticError("exact failed: No active goals remain.")

    manager.close_goal(expr)
