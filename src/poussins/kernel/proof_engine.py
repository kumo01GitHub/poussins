"""
"""

from collections import deque

from ..errors.kernel_error import KernelTypeError, KernelStateError, KernelValueError

from ..ast import ProofTerm, Formula
from ..ast.ops import collect_meta_var_ids, substitute_meta_var
from .proof_state import ProofState
from .goal import Goal, Context, ProofAssurance
from .typecheck import infer_formula, check_formula


class ProofEngine:
    """Proof engine: manages the proof state and applies inference rules to manipulate goals."""

    def __init__(self, root_formula: Formula):
        self.goal = Goal(formula=root_formula, context=Context(hyps={}))
        self.state = ProofState(goals=deque([self.goal]))

    @property
    def is_closed(self) -> bool:
        return self.state.is_closed and self.goal.is_closed

    def close_goal(self, assignment: ProofTerm):
        current_goal = self.state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to close.")
        elif current_goal.is_closed:
            raise KernelStateError("Cannot close a closed goal.")
        elif current_goal.assignment is not None:
            raise KernelStateError("Current goal is already assigned a proof term.")
        elif current_goal.formula != infer_formula(assignment, current_goal.context):
            raise KernelStateError("Assignment does not match the goal's formula.")
        else:
            current_goal.assignment = assignment
            current_goal.assurance = ProofAssurance.VERIFIED
            closed_goals = [current_goal]
            processed_goal_ids: set[str] = set()

            while closed_goals:
                closed_goal = closed_goals.pop()
                if closed_goal.id in processed_goal_ids:
                    continue
                processed_goal_ids.add(closed_goal.id)

                for idx, goal in enumerate(self.state.goals):
                    if (
                        goal == closed_goal
                        or goal.assignment is None
                        or goal.assurance in {ProofAssurance.VERIFIED, ProofAssurance.TRUSTED}
                        or closed_goal.assignment is None
                    ):
                        continue

                    substituted = substitute_meta_var(goal.assignment, closed_goal.id, closed_goal.assignment)
                    self.state.goals[idx].assignment = substituted

                    try:
                        if check_formula(substituted, goal.formula, goal.context):
                            self.state.goals[idx].assurance = ProofAssurance.VERIFIED
                            closed_goals.append(self.state.goals[idx])
                    except KernelTypeError:
                        pass

            for goal in list(self.state.goals):
                if goal.is_closed:
                    self.state.goals.remove(goal)


    def refine_goal(self, subgoals: list[Goal], assignment: ProofTerm):
        current_goal = self.state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to refine.")
        elif current_goal.is_closed:
            raise KernelStateError("Cannot refine a closed goal.")
        elif current_goal.assignment is not None:
            raise KernelStateError("Current goal is already assigned a proof term.")
        elif not subgoals:
            raise KernelValueError("Sub-goals cannot be empty when refining a goal.")
        elif any(subgoal.assignment is not None for subgoal in subgoals):
            raise KernelValueError("Sub-goals must not be assigned a proof term when refining a goal.")
        elif assignment is None:
            raise KernelValueError("Assignment cannot be None when refining a goal.")

        subgoal_ids = {goal.id for goal in subgoals}
        meta_var_ids = collect_meta_var_ids(assignment)
        if not meta_var_ids.issubset(subgoal_ids):
            raise KernelValueError("Not all meta-variables in the assignment have corresponding sub-goals.")

        self.state.current_goal.assignment = assignment
        self.state.goals.extendleft(subgoals[::-1])

    def rotate_left(self):
        self.state.goals.rotate(-1)

    def rotate_right(self):
        self.state.goals.rotate(1)

