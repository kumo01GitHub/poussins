"""Tactics for simplifying expressions in the current goal or hypothesis."""
from __future__ import annotations

from ..ast import EConst, UnivLevelParam, substitute_expr
from ..environment import DefinitionDeclaration
from ..errors import TacticError
from ..kernel import ProofManager, normalize
from .helpers import require_current_goal, requires_active_goal


@requires_active_goal
def simpl(
    manager: ProofManager,
    hyp_name: str | None = None,
    unfolding: frozenset[str] | None = None,
) -> None:
    """Simplify the current goal or a local hypothesis by fully evaluating its terms."""
    current_goal = require_current_goal(manager, tactic_name="simpl")
    metavars = manager.current_state.metavars
    env = manager.env

    if hyp_name is None:
        target_expr = current_goal.statement
        new_expr = normalize(
            target_expr, metavars=metavars, env=env, unfolding=unfolding
        )
        manager.change_goal(new_expr)
    else:
        if not current_goal.has_local_hypothesis(hyp_name):
            raise TacticError(f"Hypothesis '{hyp_name}' not found.")
        hypothesis_expr = current_goal.context[hyp_name]
        new_expr = normalize(
            hypothesis_expr, metavars=metavars, env=env, unfolding=unfolding
        )
        manager.change_hypothesis(hyp_name, new_expr)


@requires_active_goal
def dsimp(
    manager: ProofManager,
    hyp_name: str | None = None,
    unfolding: frozenset[str] | None = None,
) -> None:
    """Definitional simplify without expanding unnecessary definitions."""
    simpl(manager, hyp_name=hyp_name, unfolding=unfolding)


@requires_active_goal
def unfold(
    manager: ProofManager,
    name: str,
    hyp_name: str | None = None,
) -> None:
    """Unfold a specific definition without evaluation."""
    current_goal = require_current_goal(manager, tactic_name="unfold")

    decl = manager.env.get(name) if manager.env is not None else None
    if not isinstance(decl, DefinitionDeclaration):
        raise TacticError(f"'{name}' is not a valid definition in the environment.")

    target_const = EConst(name, tuple(UnivLevelParam(p) for p in decl.level_params))
    replacement_value = decl.value

    if hyp_name is None:
        target_expr = current_goal.statement
    else:
        if not current_goal.has_local_hypothesis(hyp_name):
            raise TacticError(f"Hypothesis '{hyp_name}' not found.")
        target_expr = current_goal.context[hyp_name]

    new_expr = substitute_expr(target_expr, target_const, replacement_value)
    if new_expr == target_expr:
        raise TacticError(f"Did not find occurrences of definition '{name}'.")

    if hyp_name is None:
        manager.change_goal(new_expr)
    else:
        manager.change_hypothesis(hyp_name, new_expr)
