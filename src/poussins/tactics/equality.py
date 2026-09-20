"""Equality tactics including reflexivity and symmetry."""
from __future__ import annotations

from ..ast import EMetaVar, Expr
from ..environment.library import EqualityDeclaration
from ..errors import TacticError
from ..kernel import Goal, ProofManager, is_def_eq, whnf
from .apply import apply
from .helpers import (
    build_app,
    const_from_decl,
    require_current_goal,
    requires_active_goal,
    split_eq_app,
)


@requires_active_goal
def reflexivity(manager: ProofManager) -> None:
    """Solves a goal of the form `Eq A x y` where `x` and `y` are equal."""
    state = manager.current_state
    current_goal = require_current_goal(manager, tactic_name="reflexivity")

    target = current_goal.statement
    context = current_goal.context
    metavars = state.metavars
    env = manager.env

    eq_args = split_eq_app(
        whnf(target, metavars, env),
        EqualityDeclaration.EQ_DECLARATION.declaration.name
    )

    if eq_args is None:
        raise TacticError("Goal is not an equality.")

    _, lhs, rhs = eq_args

    if not is_def_eq(lhs, rhs, context, metavars, env):
        raise TacticError("LHS and RHS are not definitionally equal.")

    apply(
        manager,
        const_from_decl(
            EqualityDeclaration.EQ_REFL_DECLARATION.declaration,
            manager
        )
    )

# Alias for reflexivity tactic
rfl = reflexivity


@requires_active_goal
def symmetry(manager: ProofManager) -> None:
    """Swap the left and right sides of an equality goal."""
    current_goal = require_current_goal(manager, tactic_name="symmetry")

    target = current_goal.statement
    metavars = manager.current_state.metavars
    env = manager.env

    eq_args = split_eq_app(
        whnf(target, metavars, env),
        EqualityDeclaration.EQ_DECLARATION.declaration.name
    )

    if eq_args is None:
        raise TacticError("Goal is not an equality.")

    type_a, lhs, rhs = eq_args

    eq_const = const_from_decl(
        EqualityDeclaration.EQ_DECLARATION.declaration, manager
    )
    eq_symm_const = const_from_decl(
        EqualityDeclaration.EQ_SYMM_DECLARATION.declaration, manager
    )

    new_goal = Goal(
        statement=build_app(eq_const, type_a, rhs, lhs),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )
    manager.refine_goal(
        build_app(eq_symm_const, type_a, rhs, lhs, EMetaVar(new_goal.id)),
        [new_goal]
    )

# Alias for symmetry tactic
symm = symmetry


@requires_active_goal
def transitivity(manager: ProofManager, middle: Expr) -> None:
    """Split an equality goal into two subgoals using a middle term."""
    current_goal = require_current_goal(manager, tactic_name="transitivity")

    eq_args = split_eq_app(
        whnf(
            current_goal.statement,
            manager.current_state.metavars,
            manager.env
        ),
        EqualityDeclaration.EQ_DECLARATION.declaration.name,
    )

    if eq_args is None:
        raise TacticError("Goal is not an equality.")

    type_a, lhs, rhs = eq_args

    eq_const = const_from_decl(
        EqualityDeclaration.EQ_DECLARATION.declaration, manager
    )
    eq_trans_const = const_from_decl(
        EqualityDeclaration.EQ_TRANS_DECLARATION.declaration, manager
    )

    goal1 = Goal(
        statement=build_app(eq_const, type_a, lhs, middle),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    goal2 = Goal(
        statement=build_app(eq_const, type_a, middle, rhs),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    proof = build_app(
        eq_trans_const,
        type_a,
        lhs,
        middle,
        rhs,
        EMetaVar(goal1.id),
        EMetaVar(goal2.id),
    )

    manager.refine_goal(proof, [goal1, goal2])

# Alias for transitivity tactic
trans = transitivity
