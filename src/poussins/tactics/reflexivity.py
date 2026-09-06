"""Equality tactics including reflexivity and rfl."""
from __future__ import annotations

from ..ast import EConst, UnivLevelParam
from ..environment.library import EqualityDeclaration
from ..errors import TacticError
from ..kernel import ProofManager, is_def_eq, whnf
from .apply import apply
from .helpers import require_current_goal, requires_active_goal, split_eq_app


@requires_active_goal
def reflexivity(manager: ProofManager) -> None:
    """Solves a goal of the form `Eq A x y` where `x` and `y` are equal."""
    state = manager.current_state
    current_goal = require_current_goal(manager, tactic_name="reflexivity")

    target = current_goal.statement
    context = current_goal.context
    metavars = state.metavars
    definitions = manager.env

    goal_type = whnf(target, metavars, definitions)
    eq_name = EqualityDeclaration.EQ_DECLARATION.declaration.name
    eq_args = split_eq_app(goal_type, eq_name)

    if eq_args is None:
        head_name = getattr(goal_type, "name", None)
        raise TacticError(f"Goal is not an equality. Found '{head_name}'.")

    _, x, y = eq_args

    if not is_def_eq(x, y, context, metavars, definitions):
        raise TacticError("LHS and RHS are not definitionally equal.")

    refl_decl = EqualityDeclaration.EQ_REFL_DECLARATION.declaration
    refl_const = EConst(
        name=refl_decl.name,
        levels=tuple(UnivLevelParam(param) for param in refl_decl.level_params)
    )

    apply(manager, refl_const)


# Alias for reflexivity tactic
rfl = reflexivity
