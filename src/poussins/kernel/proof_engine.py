"""
"""

from collections import deque
from copy import deepcopy

from ..ast import (
    ProofTerm, PMetaVar, PVar, PLam, PApp, PAndI, PAndE1, PAndE2, POrIL, POrIR, PTrueI, POrE, PFalseE, PExI, PExE,
    Formula, FImpl, FAnd, FOr, FTrue, FFalse, FExists
)
from .proof_state import ProofState
from .goal import Goal, Context, ProofAssurance


class ProofEngine:
    """Proof engine: manages the proof state and applies inference rules to manipulate goals."""

    def __init__(self, root_formula: Formula):
        self.goal = Goal(formula=root_formula, context=Context(hyps={}))
        self.state = ProofState(goals=deque([self.goal]))

    @property
    def is_closed(self) -> bool:
        return self.state.is_closed and self.goal.is_closed and self.goal.assurance == ProofAssurance.VERIFIED

    def close_goal(self, assignment: ProofTerm):
        current_goal = self.state.current_goal
        if current_goal is None:
            raise ValueError("No active goal to close.")
        elif current_goal.is_closed:
            raise ValueError("Cannot close a closed goal.")
        elif current_goal.assignment is not None:
            raise ValueError("Current goal is already assigned a proof term.")
        elif current_goal.formula != ProofEngine._infer_formula(assignment, current_goal.context):
            raise ValueError("Assignment does not match the goal's formula.")
        else:
            current_goal.assignment = assignment
            current_goal.assurance = ProofAssurance.VERIFIED
            self._close_subgoals(current_goal)

    def refine_goal(self, subgoals: list[Goal], assignment: ProofTerm):
        current_goal = self.state.current_goal
        if current_goal is None:
            raise ValueError("No active goal to refine.")
        elif current_goal.is_closed:
            raise ValueError("Cannot refine a closed goal.")
        elif current_goal.assignment is not None:
            raise ValueError("Current goal is already assigned a proof term.")
        elif not subgoals:
            raise ValueError("Sub-goals cannot be empty when refining a goal.")
        elif any(subgoal.assignment is not None for subgoal in subgoals):
            raise ValueError("Sub-goals must not be assigned a proof term when refining a goal.")
        elif assignment is None:
            raise ValueError("Assignment cannot be None when refining a goal.")
        elif not ProofEngine._has_all_meta_vars_subgoals(subgoals, assignment):
            raise ValueError("Not all meta-variables in the assignment have corresponding sub-goals.")

        self.state.current_goal.assignment = assignment
        self.state.goals.extendleft(subgoals[::-1])

    def rotate_left(self):
        self.state.goals.rotate(-1)

    def rotate_right(self):
        self.state.goals.rotate(1)

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

    def _close_subgoals(self, closed_goal: Goal):
        if not closed_goal.is_closed:
            raise ValueError("Cannot close sub-goals of an open goal.")
        else:
            self.state.goals.remove(closed_goal)

        closed_goals: list[Goal] = []
        for goal in list(self.state.goals):
            goal.assignment = ProofEngine._substitute_meta_var(closed_goal, goal.assignment)
            if goal.is_closed and goal not in closed_goals:
                goal.assurance = ProofAssurance.VERIFIED
                closed_goals.append(goal)

        for closed_goal in closed_goals:
            self._close_subgoals(closed_goal)

    @staticmethod
    def _infer_formula(term: ProofTerm, context: Context) -> Formula:
        match term:
            case PMetaVar(goal_id):
                raise ValueError("Cannot infer formula of a meta-variable.")
            case PVar(name):
                formula = context.get(name)
                if formula is None:
                    raise ValueError(f"Variable {name} not found in context.")
                return formula
            case PLam(var, dom, body):
                ctx = context.add({var: dom})
                return FImpl(dom, ProofEngine._infer_formula(body, ctx))
            case PApp(fn, arg):
                fn_formula = ProofEngine._infer_formula(fn, context)
                arg_formula = ProofEngine._infer_formula(arg, context)
                if not isinstance(fn_formula, FImpl):
                    raise ValueError("Cannot apply a non-function term.")
                elif fn_formula.antecedent != arg_formula:
                    raise ValueError("Argument formula does not match function's domain.")
                else:
                    return fn_formula.consequent
            case PAndI(left, right):
                left_formula = ProofEngine._infer_formula(left, context)
                right_formula = ProofEngine._infer_formula(right, context)
                return FAnd(left_formula, right_formula)
            case PAndE1(inner):
                inner_formula = ProofEngine._infer_formula(inner, context)
                if not isinstance(inner_formula, FAnd):
                    raise ValueError("PAndE1 expects conjunction.")
                return inner_formula.left
            case PAndE2(inner):
                inner_formula = ProofEngine._infer_formula(inner, context)
                if not isinstance(inner_formula, FAnd):
                    raise ValueError("PAndE2 expects conjunction.")
                return inner_formula.right
            case POrIL(pf, right_type):
                left_formula = ProofEngine._infer_formula(pf, context)
                return FOr(left_formula, right_type)
            case POrIR(left_type, pf):
                right_formula = ProofEngine._infer_formula(pf, context)
                return FOr(left_type, right_formula)
            case PTrueI():
                return FTrue()
            case POrE(disj, left_var, left_branch, right_var, right_branch):
                disj_formula = ProofEngine._infer_formula(disj, context)
                if not isinstance(disj_formula, FOr):
                    raise ValueError("POrE expects disjunction.")
                left_ctx = context.add({left_var: disj_formula.left})
                left_branch_formula = ProofEngine._infer_formula(left_branch, left_ctx)
                right_ctx = context.add({right_var: disj_formula.right})
                right_branch_formula = ProofEngine._infer_formula(right_branch, right_ctx)
                if left_branch_formula != right_branch_formula:
                    raise ValueError("Branches of POrE must yield the same formula.")
                return left_branch_formula
            case PFalseE(inner, conclusion):
                inner_formula = ProofEngine._infer_formula(inner, context)
                if not isinstance(inner_formula, FFalse):
                    raise ValueError("PFalseE expects proof of False.")
                return conclusion
            case PExI(exists_var, body, witness, pf):
                return FExists(exists_var, body)
            case PExE(pf, prop_var, hyp_var, body):
                pf_formula = ProofEngine._infer_formula(pf, context)
                if not isinstance(pf_formula, FExists):
                    raise ValueError("PExE expects proof of an existential.")
                new_ctx = context.add({hyp_var: pf_formula.body})
                return ProofEngine._infer_formula(body, new_ctx)
            case _:
                raise NotImplementedError(f"Unknown proof term: {term}")

    @staticmethod
    def _has_all_meta_vars_subgoals(subgoals: list[Goal], assignment: ProofTerm) -> bool:
        match assignment:
            case PMetaVar(goal_id):
                return any(goal.id == goal_id for goal in subgoals)
            case PLam(var, dom, body):
                return ProofEngine._has_all_meta_vars_subgoals(subgoals, body)
            case PApp(fn, arg):
                return (
                    ProofEngine._has_all_meta_vars_subgoals(subgoals, fn)
                    and ProofEngine._has_all_meta_vars_subgoals(subgoals, arg)
                )
            case PAndI(left, right):
                return (
                    ProofEngine._has_all_meta_vars_subgoals(subgoals, left)
                    and ProofEngine._has_all_meta_vars_subgoals(subgoals, right)
                )
            case PAndE1(inner):
                return ProofEngine._has_all_meta_vars_subgoals(subgoals, inner)
            case PAndE2(inner):
                return ProofEngine._has_all_meta_vars_subgoals(subgoals, inner)
            case POrIL(pf, right_type):
                return ProofEngine._has_all_meta_vars_subgoals(subgoals, pf)
            case POrIR(left_type, pf):
                return ProofEngine._has_all_meta_vars_subgoals(subgoals, pf)
            case POrE(disj, left_var, left_branch, right_var, right_branch):
                return (
                    ProofEngine._has_all_meta_vars_subgoals(subgoals, disj)
                    and ProofEngine._has_all_meta_vars_subgoals(subgoals, left_branch)
                    and ProofEngine._has_all_meta_vars_subgoals(subgoals, right_branch)
                )
            case PFalseE(inner, conclusion):
                return ProofEngine._has_all_meta_vars_subgoals(subgoals, inner)
            case PExI(exists_var, body, witness, pf):
                return ProofEngine._has_all_meta_vars_subgoals(subgoals, pf)
            case PExE(pf, prop_var, hyp_var, body):
                return (
                    ProofEngine._has_all_meta_vars_subgoals(subgoals, pf)
                    and ProofEngine._has_all_meta_vars_subgoals(subgoals, body)
                )
            case _:
                return True
