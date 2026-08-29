"""
Tactics for basic logical transformations.
"""
from __future__ import annotations

from ..ast import EApp, EConst, ELam, EMetaVar, UnivLevelParam
from ..errors import TacticError
from ..kernel import ProofManager, Goal
from ..environment import RecursorDeclaration
from ..environment.library import LogicDeclaration


def exfalso(manager: ProofManager) -> None:
    """
    Replace the current goal with False and derive the target from it using False.rec.
    """
    if manager.is_closed:
        raise TacticError("No active goals remain.")

    current_goal = manager.current_state.current_goal
    if current_goal is None:
        raise TacticError("No active goals remain.")

    false_rec_decl = LogicDeclaration.FALSE_REC_DECLARATION.declaration
    if not isinstance(false_rec_decl, RecursorDeclaration):
        raise TacticError("False.rec is not a RecursorDeclaration.")

    false_goal = Goal(
        statement=EConst("False", ()),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    elim_expr = EApp(
        EApp(
            EConst(
                name=false_rec_decl.name,
                levels=tuple(
                    UnivLevelParam(param) for param in false_rec_decl.level_params
                ),
            ),
            ELam("_", EConst("False", ()), current_goal.statement),
        ),
        EMetaVar(false_goal.id),
    )

    manager.refine_goal(elim_expr, [false_goal])
