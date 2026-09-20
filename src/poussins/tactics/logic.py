"""Tactics for basic logical transformations."""
from __future__ import annotations

from ..ast import EApp, ELam, EMetaVar
from ..environment.library import LogicDeclaration
from ..kernel import Goal, ProofManager
from .helpers import const_from_decl, require_current_goal, requires_active_goal


@requires_active_goal
def exfalso(manager: ProofManager) -> None:
    """Replace the current goal with False and derive the target from it."""
    current_goal = require_current_goal(manager)

    false_goal = Goal(
        statement=const_from_decl(
            LogicDeclaration.FALSE_DECLARATION.declaration,
            manager
        ),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    elim_expr = EApp(
        EApp(
            const_from_decl(
                LogicDeclaration.FALSE_REC_DECLARATION.declaration,
                manager
            ),
            ELam(
                "_",
                const_from_decl(
                    LogicDeclaration.FALSE_DECLARATION.declaration,
                    manager
                ),
                current_goal.statement
            ),
        ),
        EMetaVar(false_goal.id),
    )

    manager.refine_goal(elim_expr, [false_goal])
