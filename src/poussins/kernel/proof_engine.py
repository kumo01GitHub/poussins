"""
"""

from collections import deque
from copy import deepcopy
from typing import Optional

from ..ast import Formula, ProofTerm, PMetaVar, PLam, PApp, PAndI, PAndE1, PAndE2, POrIL, POrIR, POrE, PFalseE, PExE
from .proof_state import ProofState
from .goal import Goal, Context, ProofAssurance


class ProofEngine:
    """Proof engine: manages the proof state and applies inference rules to manipulate goals."""

    def __init__(self, root_formula: Formula):
        self.goal = Goal(formula=root_formula, context=Context(hyps={}))
        self.state = ProofState(goals=deque([self.goal]))

    @staticmethod
    def _substitute_meta_var(closed_goal: Goal, term: ProofTerm) -> ProofTerm:
        if not closed_goal.is_closed:
            return term
        elif isinstance(term, PMetaVar) and term.goal_id == closed_goal.id:
            return deepcopy(closed_goal.assignment)
        else:
            match term:
                case PLam():
                    term.body = ProofEngine._substitute_meta_var(closed_goal, term.body)
                case PApp():
                    term.fn = ProofEngine._substitute_meta_var(closed_goal, term.fn)
                    term.arg = ProofEngine._substitute_meta_var(closed_goal, term.arg)
                case PAndI():
                    term.left = ProofEngine._substitute_meta_var(closed_goal, term.left)
                    term.right = ProofEngine._substitute_meta_var(closed_goal, term.right)
                case PAndE1():
                    term.inner = ProofEngine._substitute_meta_var(closed_goal, term.inner)
                case PAndE2():
                    term.inner = ProofEngine._substitute_meta_var(closed_goal, term.inner)
                case POrIL():
                    term.pf = ProofEngine._substitute_meta_var(closed_goal, term.pf)
                case POrIR():
                    term.pf = ProofEngine._substitute_meta_var(closed_goal, term.pf)
                case POrE():
                    term.disj = ProofEngine._substitute_meta_var(closed_goal, term.disj)
                    term.left_branch = ProofEngine._substitute_meta_var(closed_goal, term.left_branch)
                    term.right_branch = ProofEngine._substitute_meta_var(closed_goal, term.right_branch)
                case PFalseE():
                    term.inner = ProofEngine._substitute_meta_var(closed_goal, term.inner)
                case PExE():
                    term.pf = ProofEngine._substitute_meta_var(closed_goal, term.pf)
                    term.body = ProofEngine._substitute_meta_var(closed_goal, term.body)

            return term

    
    def _close_sub_goals(self, closed_goal: Goal):
        if not closed_goal.is_closed:
            raise ValueError("Cannot close sub-goals of an open goal.")
        else:
            self.state.goals.remove(closed_goal)

        closed_goals: list[Goal] = []
        for goal in list(self.state.goals):
            goal.assignment = ProofEngine._substitute_meta_var(closed_goal, goal.assignment)
            if goal.is_closed and goal not in closed_goals:
                closed_goals.append(goal)

        for closed_goal in closed_goals:
            self._close_sub_goals(closed_goal)

    def close_goal(self, assignment: ProofTerm):
        current_goal = self.state.current_goal
        if current_goal is None:
            raise ValueError("No active goal to close.")
        elif current_goal.assignment is not None:
            raise ValueError("Current goal is already assigned a proof term.")
        elif assignment.has_meta_var:
            raise ValueError("Cannot close goal with a proof term containing meta-variables.")
        else:
            current_goal.assignment = assignment
            self._close_sub_goals(current_goal)

    def refine_goal(self, sub_goals: list[Goal], assignment: Optional[ProofTerm] = None):
        if assignment is not None:
            self.state.current_goal.assignment = assignment
        self.state.goals.extendleft(sub_goals[::-1])

    def rotate_left(self):
        self.state.goals.rotate(-1)

    def rotate_right(self):
        self.state.goals.rotate(1)

    @property
    def is_closed(self) -> bool:
        return self.state.is_closed and self.goal.is_closed
