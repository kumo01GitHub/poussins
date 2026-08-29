"""
Equality tactics including reflexivity and rfl.
"""
from __future__ import annotations

from .apply import apply
from ..ast import EApp, EConst, UnivLevelParam
from ..errors import TacticError
from ..kernel import ProofManager, is_def_eq, whnf
from ..environment.library import EqualityDeclaration


def reflexivity(manager: ProofManager) -> None:
    """
    Solves a goal of the form `Eq A x y` where `x` and `y` are definitionally equal.
    """
    if manager.is_closed:
        raise TacticError("reflexivity failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    if current_goal is None:
        raise TacticError("reflexivity failed: No active goals remain.")

    target = current_goal.statement
    context = current_goal.context
    metavars = state.metavars
    definitions = manager.env

    goal_type = whnf(target, metavars, definitions)

    raw_args = []
    head_expr = goal_type
    while isinstance(head_expr, EApp):
        raw_args.append(head_expr.arg)
        head_expr = head_expr.fn

    args = list(reversed(raw_args))

    head_name = getattr(head_expr, "name", None)
    eq_name = EqualityDeclaration.EQ_DECLARATION.declaration.name

    if head_name != eq_name or len(args) < 3:
        raise TacticError(f"reflexivity failed: Goal is not an equality. Found '{head_name}'.")

    x = args[1]
    y = args[2]

    if not is_def_eq(x, y, context, metavars, definitions):
        raise TacticError("reflexivity failed: LHS and RHS are not definitionally equal.")

    refl_decl = EqualityDeclaration.EQ_REFL_DECLARATION.declaration
    refl_const = EConst(
        name=refl_decl.name,
        levels=tuple(UnivLevelParam(param) for param in refl_decl.level_params)
    )

    apply(manager, refl_const)


# Alias for reflexivity tactic
rfl = reflexivity
