"""
Kernel: Proof Engine
This module is responsible for managing the proof state, including goals and metavariables.
"""
from __future__ import annotations

from .proof_state import ProofState, MetaVar
from .goal import Goal
from .typecheck import infer_type, unify
from ..ast import Expr, collect_meta_var_ids
from ..environment import Environment
from ..errors import KernelStateError, KernelValueError


class ProofEngine:
    def __init__(self, env: Environment):
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

        candidate_metavars = state.metavars | {
            current_goal.id: MetaVar(statement=current_goal.statement, assignment=assignment)
        }
        inferred_type = infer_type(assignment, current_goal.context, candidate_metavars)
        final_metavars = unify(inferred_type, current_goal.statement, current_goal.context, candidate_metavars)
        remaining_goals = [g for g in state.goals[1:] if not final_metavars[g.id].is_assigned]

        return ProofState(goals=tuple(remaining_goals), metavars=final_metavars)

    def refine_goal(self, state: ProofState, assignment: Expr, subgoals: list[Goal]) -> ProofState:
        """
        Refine the current goal by providing an assignment that splits it into new subgoals.
        """
        current_goal = state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to refine.")

        candidate_metavars = state.metavars | {g.id: MetaVar(statement=g.statement) for g in subgoals}
        candidate_metavars[current_goal.id] = MetaVar(statement=current_goal.statement, assignment=assignment)

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

        inferred_type = infer_type(assignment, current_goal.context, candidate_metavars)

        final_metavars = unify(inferred_type, current_goal.statement, current_goal.context, candidate_metavars)

        all_potential_goals = subgoals + list(state.goals[1:])
        truly_active_goals = [g for g in all_potential_goals if not final_metavars[g.id].is_assigned]

        return ProofState(goals=tuple(truly_active_goals), metavars=final_metavars)
