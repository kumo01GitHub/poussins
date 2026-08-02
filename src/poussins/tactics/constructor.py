"""
Tactic for applying inductive constructors.
"""
from __future__ import annotations

from .apply import apply
from ..ast import EConst, EApp, EPi
from ..errors import TacticError
from ..kernel import ProofManager, whnf, infer_type
from ..environment import Environment, InductiveDeclaration, ConstructorDeclaration


def constructor(manager: ProofManager, index: int | None = None) -> None:
    """
    Apply a matching constructor, or the constructor at the given index.
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

    head_name = getattr(head_expr, "name", None)
    if not head_name:
        raise TacticError(f"constructor failed: Goal type head has no name. Found: {goal_type}")

    env = manager.env
    inductive_decl = env.get(head_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(f"constructor failed: '{head_name}' is not an inductive type.")
    elif not inductive_decl.constructor_names:
        raise TacticError(f"constructor failed: Inductive type '{head_name}' has no constructors.")

    if index is not None:
        if not (1 <= index <= len(inductive_decl.constructor_names)):
            raise TacticError(
                f"constructor failed: Invalid constructor index {index} for '{head_name}'. "
                f"Expected 1..{len(inductive_decl.constructor_names)}."
            )
        target_name = inductive_decl.constructor_names[index - 1]
        decl = env.get(target_name)
        if not isinstance(decl, ConstructorDeclaration):
            raise TacticError(f"constructor failed: '{target_name}' is not a constructor declaration.")

        apply(manager, EConst(name=target_name, levels=decl.level_params))
        return

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

        c_head_name = getattr(c_head, "name", None)
        if c_head_name == head_name:
            matched_constructor_const = const
            break

    if matched_constructor_const is None:
        raise TacticError(f"constructor failed: No constructor of '{head_name}' matches the goal structure.")

    apply(manager, matched_constructor_const)


def _goal_head_name(manager: ProofManager) -> str:
    """
    Resolve the head constant name of the current goal type.
    """
    state = manager.current_state
    current_goal = state.current_goal
    if current_goal is None:
        raise TacticError("constructor failed: No active goals remain.")

    goal_type = whnf(current_goal.statement, state.metavars)

    head_expr = goal_type
    while isinstance(head_expr, EApp):
        head_expr = head_expr.fn

    head_name = getattr(head_expr, "name", None)
    if not head_name:
        raise TacticError(f"constructor failed: Goal type head has no name. Found: {goal_type}")
    return head_name


def _apply_named_constructor(
    manager: ProofManager,
    *,
    inductive_name: str,
    constructor_name: str,
    tactic_name: str,
) -> None:
    """
    Apply a specific constructor of an expected inductive goal.
    """
    head_name = _goal_head_name(manager)
    if head_name != inductive_name:
        if tactic_name == "left" or tactic_name == "right":
            raise TacticError(f"{tactic_name} failed: Goal is not a disjunction. Found head '{head_name}'.")
        if tactic_name == "split":
            raise TacticError(f"split failed: Goal is not a conjunction. Found head '{head_name}'.")
        raise TacticError(f"{tactic_name} failed: Goal head '{head_name}' does not match '{inductive_name}'.")

    env = manager.env
    inductive_decl = env.get(inductive_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(f"{tactic_name} failed: '{inductive_name}' is not an inductive type.")
    if constructor_name not in inductive_decl.constructor_names:
        raise TacticError(
            f"{tactic_name} failed: '{constructor_name}' is not a constructor of '{inductive_name}'."
        )

    decl = env.get(constructor_name)
    if not isinstance(decl, ConstructorDeclaration):
        raise TacticError(f"{tactic_name} failed: '{constructor_name}' is not a constructor declaration.")

    apply(manager, EConst(name=constructor_name, levels=decl.level_params))


def left(manager: ProofManager) -> None:
    """
    Prove an `Or` goal by selecting the left constructor (`Or.inl`).
    """
    if manager.is_closed:
        raise TacticError("left failed: No active goals remain.")

    _apply_named_constructor(
        manager,
        inductive_name=Environment.OR_DECLARATION.name,
        constructor_name=Environment.OR_INL_DECLARATION.name,
        tactic_name="left",
    )


def right(manager: ProofManager) -> None:
    """
    Prove an `Or` goal by selecting the right constructor (`Or.inr`).
    """
    if manager.is_closed:
        raise TacticError("right failed: No active goals remain.")

    _apply_named_constructor(
        manager,
        inductive_name=Environment.OR_DECLARATION.name,
        constructor_name=Environment.OR_INR_DECLARATION.name,
        tactic_name="right",
    )


def split(manager: ProofManager) -> None:
    """
    Prove an `And` goal by applying `And.intro`.
    """
    if manager.is_closed:
        raise TacticError("split failed: No active goals remain.")

    _apply_named_constructor(
        manager,
        inductive_name=Environment.AND_DECLARATION.name,
        constructor_name=Environment.AND_INTRO_DECLARATION.name,
        tactic_name="split",
    )
