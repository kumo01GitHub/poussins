"""Equality tactics including reflexivity and symmetry."""
from __future__ import annotations

from ..ast import EMetaVar, Expr, app
from ..environment import const
from ..environment.library import EQ_IND_SPEC, EQ_SYMM_DEF_SPEC, EQ_TRANS_DEF_SPEC
from ..errors import TacticError
from ..kernel import Goal, ProofManager, is_def_eq, whnf
from .apply import apply
from .helpers import (
    parse_eq_app,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def reflexivity(manager: ProofManager) -> None:
    """Solves a goal of the form `Eq A x y` where `x` and `y` are equal."""
    current_goal = require_current_goal(manager, tactic_name="reflexivity")
    metavars = manager.current_state.metavars
    env = manager.env

    eq_args = parse_eq_app(
        whnf(current_goal.statement, metavars, env),
    )

    if eq_args is None:
        raise TacticError("Goal is not an equality.")

    _, lhs, rhs = eq_args

    if not is_def_eq(lhs, rhs, current_goal.context, metavars, env):
        raise TacticError("LHS and RHS are not definitionally equal.")

    apply(
        manager,
        const(env=manager.env, name=EQ_IND_SPEC.constructors[0][0])
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

    eq_args = parse_eq_app(
        whnf(target, metavars, env),
    )

    if eq_args is None:
        raise TacticError("Goal is not an equality.")

    type_a, lhs, rhs = eq_args

    eq_const = const(env=manager.env, name=EQ_IND_SPEC.name)
    eq_symm_const = const(env=manager.env, name=EQ_SYMM_DEF_SPEC.name)

    new_goal = Goal(
        statement=app(eq_const, type_a, rhs, lhs),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )
    manager.refine_goal(
        app(eq_symm_const, type_a, rhs, lhs, EMetaVar(new_goal.id)),
        [new_goal]
    )

# Alias for symmetry tactic
symm = symmetry


@requires_active_goal
def transitivity(manager: ProofManager, term: Expr) -> None:
    """Split an equality goal into two subgoals using a middle term."""
    current_goal = require_current_goal(manager, tactic_name="transitivity")

    eq_args = parse_eq_app(
        whnf(
            current_goal.statement,
            manager.current_state.metavars,
            manager.env
        ),
    )

    if eq_args is None:
        raise TacticError("Goal is not an equality.")

    type_a, lhs, rhs = eq_args

    eq_const = const(env=manager.env, name=EQ_IND_SPEC.name)
    eq_trans_const = const(env=manager.env, name=EQ_TRANS_DEF_SPEC.name)

    goal1 = Goal(
        statement=app(eq_const, type_a, lhs, term),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    goal2 = Goal(
        statement=app(eq_const, type_a, term, rhs),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    proof = app(
        eq_trans_const,
        type_a,
        lhs,
        term,
        rhs,
        EMetaVar(goal1.id),
        EMetaVar(goal2.id),
    )

    manager.refine_goal(proof, [goal1, goal2])

# Alias for transitivity tactic
trans = transitivity
