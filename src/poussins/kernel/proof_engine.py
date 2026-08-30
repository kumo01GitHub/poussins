"""Kernel-level proof engine for managing proof states, goals, and metavariables.
"""
from __future__ import annotations

from ..ast import Expr, collect_metavar_ids
from ..environment import Environment
from ..errors import KernelStateError, KernelValueError
from .equality import is_def_eq
from .goal import Goal
from .proof_state import MetaVar, ProofState
from .typecheck import infer_type
from .unification import unify


class ProofEngine:
    """Validate proof-state transitions against the current environment.
    """

    def create_initial_state(self, statement: Expr, env: Environment) -> ProofState:
        """Create the initial proof state with a single goal and its corresponding metavariable.
        """
        initial_goal = Goal(
            statement=statement,
            context=env.to_context(),
            local_hypothesis_names=frozenset(),
        )
        initial_metavars = {initial_goal.id: MetaVar(statement=statement)}
        return ProofState(goals=(initial_goal,), metavars=initial_metavars)

    def close_goal(self, state: ProofState, assignment: Expr, env: Environment) -> ProofState:
        """Close the current goal by providing an assignment that satisfies the goal's statement.
        """
        current_goal = state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to close.")

        candidate_metavars = state.metavars | {
            current_goal.id: MetaVar(
                statement=current_goal.statement, assignment=assignment
            )
        }
        inferred_type = infer_type(
            assignment,
            current_goal.context,
            candidate_metavars,
            env,
        )
        final_metavars = unify(
            inferred_type,
            current_goal.statement,
            current_goal.context,
            candidate_metavars,
            env,
        )

        remaining_goals = [
            g for g in state.goals[1:] if not final_metavars[g.id].is_assigned
        ]
        return ProofState(goals=tuple(remaining_goals), metavars=final_metavars)

    def refine_goal(
        self, state: ProofState, assignment: Expr, subgoals: list[Goal], env: Environment
    ) -> ProofState:
        """Refine the current goal by providing an assignment that splits it into new subgoals.
        """
        current_goal = state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to refine.")

        candidate_metavars = state.metavars | {
            g.id: MetaVar(statement=g.statement) for g in subgoals
        }
        candidate_metavars[current_goal.id] = MetaVar(
            statement=current_goal.statement, assignment=assignment
        )

        assigned_metavar_ids = {
            mid for mid, m in state.metavars.items() if m.is_assigned
        }
        metavar_ids_in_expr = collect_metavar_ids(assignment)
        active_metavar_ids = [
            mid for mid in metavar_ids_in_expr if mid not in assigned_metavar_ids
        ]
        subgoal_ids = [g.id for g in subgoals]

        if active_metavar_ids != subgoal_ids:
            raise KernelValueError(
                "Subgoal mismatch with assignment expressions.\n" +
                f"  Expected from assignment (in order): {active_metavar_ids}\n" +
                f"  Provided subgoals:                   {subgoal_ids}"
            )

        for g in subgoals:
            if g.id in state.metavars:
                raise KernelStateError(
                    f"Meta-variable ?{g.id} is already registered in the proof state."
                )

        inferred_type = infer_type(
            assignment,
            current_goal.context,
            candidate_metavars,
            env,
        )
        final_metavars = unify(
            inferred_type,
            current_goal.statement,
            current_goal.context,
            candidate_metavars,
            env,
        )

        all_potential_goals = subgoals + list(state.goals[1:])
        truly_active_goals = [
            g for g in all_potential_goals if not final_metavars[g.id].is_assigned
        ]
        return ProofState(goals=tuple(truly_active_goals), metavars=final_metavars)

    def change_goal(self, state: ProofState, new_statement: Expr, env: Environment) -> ProofState:
        """Replace the current goal statement with a definitionally equal statement."""
        current_goal = state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to change.")

        if not is_def_eq(
            new_statement,
            current_goal.statement,
            current_goal.context,
            state.metavars,
            env,
        ):
            raise KernelValueError(
                "change failed: New goal is not definitionally equal to the current goal."
            )

        updated_goal = current_goal.with_statement(new_statement)
        updated_goals = (updated_goal,) + state.goals[1:]
        current_meta = state.metavars[current_goal.id]
        updated_metavars = state.metavars | {
            current_goal.id: MetaVar(
                statement=new_statement, assignment=current_meta.assignment
            )
        }
        return ProofState(goals=updated_goals, metavars=updated_metavars)

    def change_hypothesis(
        self, state: ProofState, hypothesis_name: str, new_type: Expr, env: Environment
    ) -> ProofState:
        """Replace the type of a local hypothesis with a definitionally equal type.
        """
        current_goal = state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to change.")

        if not current_goal.has_local_hypothesis(hypothesis_name):
            raise KernelValueError(
                f"change failed: Unknown hypothesis '{hypothesis_name}'."
            )

        current_type = current_goal.local_context[hypothesis_name]
        if not is_def_eq(
            new_type,
            current_type,
            current_goal.context,
            state.metavars,
            env,
        ):
            raise KernelValueError(
                f"change failed: New type for '{hypothesis_name}' is not definitionally equal to the current type."
            )

        updated_local_context = current_goal.local_context | {
            hypothesis_name: new_type
        }
        updated_goal = current_goal.with_context(
            env.to_context() | updated_local_context,
            frozenset(updated_local_context.keys()),
        )
        updated_goals = (updated_goal,) + state.goals[1:]
        current_meta = state.metavars[current_goal.id]
        updated_metavars = state.metavars | {
            current_goal.id: MetaVar(
                statement=current_goal.statement, assignment=current_meta.assignment
            )
        }
        return ProofState(goals=updated_goals, metavars=updated_metavars)
