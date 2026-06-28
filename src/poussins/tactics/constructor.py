"""
Constructor tactic: splits conjunction goals into subgoals, and handles disjunction goals by creating a subgoal for the chosen disjunct.
"""
from copy import deepcopy

from .constants import TacticSide
from ..ast import (
    FTrue,
    FAnd,
    FOr,
    PMetaVar,
    PTrueI,
    PAndI,
    POrIL,
    POrIR
)
from ..errors import TacticError
from ..kernel import Goal, ProofEngine


def constructor(engine: ProofEngine, side: TacticSide = TacticSide.LEFT):
    """Apply the constructor tactic to split a conjunction goal into subgoals."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply constructor tactic.")

    if isinstance(current_goal.formula, FTrue):
        engine.close_goal(PTrueI())
    elif isinstance(current_goal.formula, FAnd):
        left_subgoal = Goal(
            formula=deepcopy(current_goal.formula.left),
            context=current_goal.context
        )
        right_subgoal = Goal(
            formula=deepcopy(current_goal.formula.right),
            context=current_goal.context
        )
        engine.refine_goal(
            [left_subgoal, right_subgoal],
            assignment=PAndI(
                left=PMetaVar(goal_id=left_subgoal.id),
                right=PMetaVar(goal_id=right_subgoal.id)
            )
        )
    elif isinstance(current_goal.formula, FOr):
        if side == TacticSide.LEFT:
            subgoal = Goal(
                formula=deepcopy(current_goal.formula.left),
                context=current_goal.context
            )
            engine.refine_goal(
                [subgoal],
                assignment=POrIL(
                    proof=PMetaVar(goal_id=subgoal.id),
                    other_disjunct=deepcopy(current_goal.formula.right)
                )
            )
        elif side == TacticSide.RIGHT:
            subgoal = Goal(
                formula=deepcopy(current_goal.formula.right),
                context=current_goal.context
            )
            engine.refine_goal(
                [subgoal],
                assignment=POrIR(
                    other_disjunct=deepcopy(current_goal.formula.left),
                    proof=PMetaVar(goal_id=subgoal.id)
                )
            )
        else:
            raise TacticError("Constructor tactic for disjunction requires a valid side.")
    else:
        raise TacticError("Constructor tactic can only be applied to conjunctions, disjunctions, or true goals.")


def left(engine: ProofEngine):
    constructor(engine, TacticSide.LEFT)


def right(engine: ProofEngine):
    constructor(engine, TacticSide.RIGHT)


def split(engine: ProofEngine):
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply constructor tactic.")
    elif not isinstance(current_goal.formula, FAnd):
        raise TacticError("Split tactic can only be applied to conjunctions.")

    constructor(engine)
