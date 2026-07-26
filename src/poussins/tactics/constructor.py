from __future__ import annotations

from .apply import apply
from ..ast import EConst, EApp, EPi
from ..errors import TacticError
from ..kernel import ProofManager, whnf, infer_type
from ..environment import InductiveDeclaration, ConstructorDeclaration


def constructor(manager: ProofManager) -> None:
    """
    Constructor tactic: Automatically find and apply a valid constructor 
    for the current inductive goal type.
    """
    if manager.is_closed:
        raise TacticError("constructor failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    assert current_goal is not None

    goal_type = whnf(current_goal.statement, state.metavars)

    head_expr = goal_type
    while isinstance(head_expr, EApp):
        head_expr = head_expr.fn

    if not isinstance(head_expr, EConst):
        raise TacticError(f"constructor failed: Goal type head is not a constant. Found: {goal_type}")

    env = manager.env
    inductive_decl = env.get(head_expr.name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(f"constructor failed: '{head_expr.name}' is not an inductive type.")
    elif not inductive_decl.constructor_names:
        raise TacticError(f"constructor failed: Inductive type '{head_expr.name}' has no constructors.")

    matched_constructor_const: EConst | None = None

    for name in inductive_decl.constructor_names:
        decl = env.get(name)
        if not isinstance(decl, ConstructorDeclaration):
            raise TacticError(f"constructor failed: '{name}' is not a constructor declaration.")

        levels = decl.level_params
        const = EConst(name=name, levels=levels)

        c_type = whnf(infer_type(const, current_goal.context, state.metavars), state.metavars)

        c_conclusion = c_type
        while isinstance(c_conclusion, EPi):
            c_conclusion = whnf(c_conclusion.body, state.metavars)
            
        c_head = c_conclusion
        while isinstance(c_head, EApp):
            c_head = c_head.fn

        if isinstance(c_head, EConst) and c_head.name == head_expr.name:
            matched_constructor_const = const
            break

    if matched_constructor_const is None:
        raise TacticError(f"constructor failed: No constructor of '{head_expr.name}' matches the goal structure.")

    apply(manager, matched_constructor_const)
