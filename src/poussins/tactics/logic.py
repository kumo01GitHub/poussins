"""Tactics for basic logical transformations."""
from __future__ import annotations

from ..ast import EApp, ELam, EMetaVar, EPi, EVar, Expr
from ..environment.library import LogicDeclaration
from ..errors import TacticError
from ..kernel import Goal, ProofManager, is_def_eq, whnf
from .helpers import const_from_decl, require_current_goal, requires_active_goal


def _build_false_elim(
    manager: ProofManager,
    current_goal: Goal,
    false_proof: Expr
) -> Expr:
    """Construct the expression to eliminate False and derive the current goal."""
    return EApp(
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
        false_proof,
    )


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

    manager.refine_goal(
        _build_false_elim(manager, current_goal, EMetaVar(false_goal.id)),
        [false_goal]
    )


@requires_active_goal
def contradiction(manager: ProofManager) -> None:
    """Close the current goal if local hypotheses contain a contradiction."""
    current_goal = require_current_goal(manager)
    local_ctx = current_goal.local_context
    env = manager.env
    metavars = manager.current_state.metavars

    false_type = const_from_decl(
        LogicDeclaration.FALSE_DECLARATION.declaration,
        manager
    )

    # Check for a direct contradiction in the local context
    for name, hyp_type in local_ctx.items():
        norm_type = whnf(hyp_type, metavars, env)
        if norm_type == false_type:
            proof = _build_false_elim(manager, current_goal, EVar(name))
            manager.close_goal(proof)
            return

    # Check for a contradiction between two hypotheses in the local context
    for name2, type2 in local_ctx.items():
        norm_type2 = whnf(type2, metavars, env)

        if isinstance(norm_type2, EPi):
            body_norm = whnf(norm_type2.body, metavars, env)
            if body_norm == false_type:
                for name1, type1 in local_ctx.items():
                    norm_type1 = whnf(type1, metavars, env)

                    if is_def_eq(
                        norm_type2.domain,
                        norm_type1,
                        context=current_goal.context,
                        metavars=metavars,
                        env=env,
                    ):
                        false_proof = EApp(EVar(name2), EVar(name1))
                        proof = _build_false_elim(manager, current_goal, false_proof)
                        manager.close_goal(proof)
                        return

    raise TacticError("No contradiction found in local context.")
