from __future__ import annotations

from ..ast import Expr
from ..errors import TacticError
from ..kernel import ProofManager

def exact(manager: ProofManager, expr: Expr) -> None:
    """
    Exact tactic: Attempt to close the current goal by providing a complete proof expression (Expr)
    that matches the goal's statement.
    """
    if manager.is_closed:
        raise TacticError("exact failed: No active goals remain.")

    try:
        manager.close_goal(expr)
    except Exception as e:
        raise TacticError(f"exact failed: {e}") from e
