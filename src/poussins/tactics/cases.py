"""
"""
from copy import deepcopy
from typing import Optional

from ..ast import LogicalSide, FAnd, FOr, PMetaVar, PAndE, POrE, PVar
from ..errors import TacticError
from ..kernel import Goal, ProofEngine


def cases(engine: ProofEngine, hyp_name: str, left_name: Optional[str] = None, right_name: Optional[str] = None):
    """Apply the cases tactic to perform case analysis on a disjunction hypothesis."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply cases tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is None:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in the current context.")

    if left_name is None:
        left_name = f"{hyp_name}{LogicalSide.LEFT.symbol}"
    if right_name is None:
        right_name = f"{hyp_name}{LogicalSide.RIGHT.symbol}"

    if isinstance(hyp, FAnd):
        subgoal = Goal(
            formula=deepcopy(current_goal.formula),
            context=current_goal.context
                .delete(hyp_name)
                .add({
                    left_name: hyp.left,
                    right_name: hyp.right
                })
        )
        engine.refine_goal(
            [subgoal],
            assignment=PAndE(
                conj_proof=PVar(name=hyp_name),
                left_hyp=left_name,
                right_hyp=right_name,
                case_proof=PMetaVar(goal_id=subgoal.id)
            )
        )
    elif isinstance(hyp, FOr):
        left_subgoal = Goal(
            formula = deepcopy(current_goal.formula),
            context = current_goal.context.delete(hyp_name).add({left_name: hyp.left})
        )
        right_subgoal = Goal(
            formula=deepcopy(current_goal.formula),
            context=current_goal.context.delete(hyp_name).add({right_name: hyp.right})
        )

        engine.refine_goal(
            [left_subgoal, right_subgoal],
            assignment=POrE(
                disj_proof=PVar(name=hyp_name),
                left_hyp=left_name,
                left_case=PMetaVar(goal_id=left_subgoal.id),
                right_hyp=right_name,
                right_case=PMetaVar(goal_id=right_subgoal.id)
            )
        )
    else:
        raise TacticError(f"Hypothesis '{hyp_name}' is not a disjunction and cannot be used with cases tactic.")
