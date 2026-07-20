"""
Kernel: Proof Engine
This module is responsible for managing the proof state, including goals and metavariables.
"""
from __future__ import annotations

from .proof_state import ProofState, MetaVar
from .goal import Goal
from .typecheck import infer_type, whnf, is_alpha_eq
from ..ast import Expr, collect_meta_var_ids
from ..errors import KernelStateError, KernelTypeError, KernelValueError

from ..environment import Environment


class ProofEngine:
    def __init__(self, env: Environment):
        self.env = env
        self.global_context = {name: decl.type for name, decl in env.items()}

    def create_initial_state(self, statement: Expr) -> ProofState:
        """
        Create the initial proof state with a single goal and its corresponding metavariable.
        """
        initial_goal = Goal(statement=statement, context=self.global_context)
        initial_metavars = {initial_goal.id: MetaVar(statement=statement)}
        return ProofState(goals=(initial_goal,), metavars=initial_metavars)

    def close_goal(self, state: ProofState, assignment: Expr) -> ProofState:
        """
        Close the current goal by providing an assignment that satisfies the goal's statement.
        """
        current_goal = state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to close.")

        new_metavars = state.metavars | {
            current_goal.id: MetaVar(statement=current_goal.statement, assignment=assignment)
        }
        new_goals = state.goals[1:]
        candidate_state = ProofState(goals=new_goals, metavars=new_metavars)

        inferred_type = infer_type(assignment, current_goal.context, candidate_state.metavars)

        if not is_alpha_eq(whnf(inferred_type, candidate_state.metavars), whnf(current_goal.statement, candidate_state.metavars)):
            raise KernelTypeError(
                f"Goal statement mismatch. "
                f"Expected: {current_goal.statement}, Found: {inferred_type}"
            )

        return candidate_state

    def refine_goal(self, state: ProofState, assignment: Expr, subgoals: list[Goal]) -> ProofState:
        """
        Refine the current goal by providing an assignment that splits it into new subgoals.
        Called by tactics (e.g., apply, intro).
        """
        current_goal = state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to refine.")

        new_metavars = state.metavars | {g.id: MetaVar(statement=g.statement) for g in subgoals}
        new_metavars[current_goal.id] = MetaVar(statement=current_goal.statement, assignment=assignment)
        new_goals = tuple(subgoals) + state.goals[1:]
        
        candidate_state = ProofState(goals=new_goals, metavars=new_metavars)

        inferred_type = infer_type(assignment, current_goal.context, candidate_state.metavars)
        if not is_alpha_eq(whnf(inferred_type, candidate_state.metavars), whnf(current_goal.statement, candidate_state.metavars)):
            raise KernelTypeError(
                f"Goal statement mismatch inside refinement. "
                f"Expected: {current_goal.statement}, Found: {inferred_type}"
            )

        meta_var_ids = collect_meta_var_ids(assignment)
        assigned_ids = {mid for mid, m in state.metavars.items() if m.is_assigned}
        active_meta_ids = meta_var_ids - assigned_ids
        other_goal_ids = {g.id for g in state.goals[1:]}

        subgoal_ids = {g.id for g in subgoals}
        untracked_ids = active_meta_ids - subgoal_ids - other_goal_ids

        if untracked_ids:
            raise KernelValueError(
                f"Found untracked or implicit meta-variables in the assignment: {untracked_ids}. "
                f"All active meta-variables in the proof term must be explicitly registered as subgoals."
            )

        if not subgoal_ids.issubset(active_meta_ids):
            raise KernelValueError("Some provided subgoals are missing from the assignment expression.")

        for g in subgoals:
            if g.id in state.metavars:
                raise KernelStateError(f"Meta-variable ?{g.id} is already registered in the proof state.")

        return candidate_state
