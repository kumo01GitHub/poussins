"""Tactic for applying inductive constructors."""
from __future__ import annotations

from ..ast import EConst, EPi, UnivLevelParam
from ..environment import ConstructorDeclaration, InductiveDeclaration
from ..environment.library import LogicDeclaration
from ..errors import TacticError
from ..kernel import ProofManager, infer_type, whnf
from .apply import apply
from .helpers import const_head_name, require_current_goal, requires_active_goal


@requires_active_goal
def constructor(manager: ProofManager, index: int | None = None) -> None:
    """Apply a matching constructor, or the constructor at the given index."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    goal_type = whnf(current_goal.statement, state.metavars, manager.env)
    head_name = const_head_name(goal_type)
    if head_name is None:
        raise TacticError(
            "Goal type head must be a constant, "
            + f"found {type(goal_type).__name__}: {goal_type}"
        )

    inductive_decl = manager.env.get(head_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(f"'{head_name}' is not an inductive type.")
    elif not inductive_decl.constructor_names:
        raise TacticError(f"Inductive type '{head_name}' has no constructors.")

    if index is not None:
        if not (1 <= index <= len(inductive_decl.constructor_names)):
            raise TacticError(
                f"Invalid constructor index {index} for '{head_name}'. "
                + f"Expected 1..{len(inductive_decl.constructor_names)}."
            )
        target_name = inductive_decl.constructor_names[index - 1]
        decl = manager.env.get(target_name)
        if not isinstance(decl, ConstructorDeclaration):
            raise TacticError(f"'{target_name}' is not a constructor declaration.")

        apply(
            manager,
            EConst(
                name=target_name,
                levels=tuple(UnivLevelParam(param) for param in decl.level_params)
            )
        )
        return

    matched_constructor_const: EConst | None = None

    for name in inductive_decl.constructor_names:
        decl = manager.env.get(name)
        if not isinstance(decl, ConstructorDeclaration):
            raise TacticError(f"'{name}' is not a constructor declaration.")

        const = EConst(
            name=name,
            levels=tuple(UnivLevelParam(param) for param in decl.level_params)
        )

        c_type = whnf(
            infer_type(const, current_goal.context, state.metavars, manager.env),
            state.metavars,
            manager.env,
        )

        c_conclusion = c_type
        while isinstance(c_conclusion, EPi):
            c_conclusion = whnf(c_conclusion.body, state.metavars, manager.env)

        c_head_name = const_head_name(c_conclusion)
        if c_head_name == head_name:
            matched_constructor_const = const
            break

    if matched_constructor_const is None:
        raise TacticError(
            f"No constructor of '{head_name}' matches the goal structure."
        )

    apply(manager, matched_constructor_const)


def _goal_head_name(manager: ProofManager) -> str:
    """Resolve the head constant name of the current goal type."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    goal_type = whnf(current_goal.statement, state.metavars, manager.env)

    head_name = const_head_name(goal_type)
    if head_name is None:
        raise TacticError(
            "Goal type head must be a constant, "
            + f"found {type(goal_type).__name__}: {goal_type}"
        )

    return head_name


def _apply_named_constructor(
    manager: ProofManager,
    *,
    inductive_name: str,
    constructor_name: str,
    tactic_name: str,
) -> None:
    """Apply a specific constructor of an expected inductive goal."""
    head_name = _goal_head_name(manager)
    if head_name != inductive_name:
        if tactic_name in {"left", "right"}:
            raise TacticError(
                f"{tactic_name} failed: "
                + f"Goal is not a disjunction. Found head '{head_name}'."
            )
        if tactic_name == "split":
            raise TacticError(
                f"split failed: Goal is not a conjunction. Found head '{head_name}'."
            )
        raise TacticError(
            f"{tactic_name} failed: "
            + f"Goal head '{head_name}' does not match '{inductive_name}'."
        )

    env = manager.env
    inductive_decl = env.get(inductive_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(
            f"{tactic_name} failed: '{inductive_name}' is not an inductive type."
        )
    if constructor_name not in inductive_decl.constructor_names:
        raise TacticError(
            f"{tactic_name} failed: "
            + f"'{constructor_name}' is not a constructor of '{inductive_name}'."
        )

    decl = env.get(constructor_name)
    if not isinstance(decl, ConstructorDeclaration):
        raise TacticError(
            f"{tactic_name} failed: "
            + f"'{constructor_name}' is not a constructor declaration."
        )

    apply(manager, EConst(
        name=constructor_name,
        levels=tuple(UnivLevelParam(param) for param in decl.level_params)
    ))


@requires_active_goal
def left(manager: ProofManager) -> None:
    """Prove an `Or` goal by selecting the left constructor (`Or.inl`)."""
    _apply_named_constructor(
        manager,
        inductive_name=LogicDeclaration.OR_DECLARATION.declaration.name,
        constructor_name=LogicDeclaration.OR_INL_DECLARATION.declaration.name,
        tactic_name="left",
    )


@requires_active_goal
def right(manager: ProofManager) -> None:
    """Prove an `Or` goal by selecting the right constructor (`Or.inr`)."""
    _apply_named_constructor(
        manager,
        inductive_name=LogicDeclaration.OR_DECLARATION.declaration.name,
        constructor_name=LogicDeclaration.OR_INR_DECLARATION.declaration.name,
        tactic_name="right",
    )


@requires_active_goal
def split(manager: ProofManager) -> None:
    """Prove an `And` goal by applying `And.intro`."""
    _apply_named_constructor(
        manager,
        inductive_name=LogicDeclaration.AND_DECLARATION.declaration.name,
        constructor_name=LogicDeclaration.AND_INTRO_DECLARATION.declaration.name,
        tactic_name="split",
    )
