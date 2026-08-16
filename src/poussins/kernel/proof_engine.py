"""
Kernel-level proof engine for managing proof states, goals, and metavariables.
"""
from __future__ import annotations

from .equality import is_def_eq
from .proof_state import ProofState, MetaVar
from .goal import Goal
from .typecheck import infer_type
from .unification import unify
from ..ast import Expr, collect_metavar_ids
from ..environment import Environment, DefinitionDeclaration
from ..errors import KernelStateError, KernelValueError


class ProofEngine:
    """
    Validate proof-state transitions against the current environment.
    """

    def __init__(self, env: Environment):
        """
        Build a proof engine with the declarations available in ``env``.
        """
        self.env = env

    @property
    def global_context(self) -> dict[str, Expr]:
        """
        Return the current global typing context from the environment.
        """
        return {name: decl.type for name, decl in self.env.items()}

    @property
    def definitions(self) -> dict[str, Expr]:
        """
        Return unfoldable definitions from the environment.
        """
        return {
            name: decl.value
            for name, decl in self.env.items()
            if isinstance(decl, DefinitionDeclaration)
        }

    def refresh_goal(self, goal: Goal) -> Goal:
        """
        Rebuild a goal so its global view matches the current environment.
        """
        return goal.with_context(
            self.global_context | goal.local_context, goal.local_hypothesis_names
        )

    def refresh_state(self, state: ProofState) -> ProofState:
        """
        Refresh all goals in a proof state against the current environment.
        """
        if not state.goals:
            return state
        return ProofState(
            goals=tuple(self.refresh_goal(goal) for goal in state.goals),
            metavars=state.metavars,
        )

    def create_initial_state(self, statement: Expr) -> ProofState:
        """
        Create the initial proof state with a single goal and its corresponding metavariable.
        """
        initial_goal = Goal(
            statement=statement,
            context=self.global_context,
            local_hypothesis_names=frozenset(),
        )
        initial_metavars = {initial_goal.id: MetaVar(statement=statement)}
        return ProofState(goals=(initial_goal,), metavars=initial_metavars)

    def close_goal(self, state: ProofState, assignment: Expr) -> ProofState:
        """
        Close the current goal by providing an assignment that satisfies the goal's statement.
        """
        state = self.refresh_state(state)
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
            self.definitions,
        )
        final_metavars = unify(
            inferred_type,
            current_goal.statement,
            current_goal.context,
            candidate_metavars,
            self.definitions,
        )

        remaining_goals = [
            g for g in state.goals[1:] if not final_metavars[g.id].is_assigned
        ]
        return ProofState(goals=tuple(remaining_goals), metavars=final_metavars)

    def refine_goal(
        self, state: ProofState, assignment: Expr, subgoals: list[Goal]
    ) -> ProofState:
        """
        Refine the current goal by providing an assignment that splits it into new subgoals.
        """
        state = self.refresh_state(state)
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
                f"Subgoal mismatch with assignment expressions.\n"
                f"  Expected from assignment (in order): {active_metavar_ids}\n"
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
            self.definitions,
        )
        final_metavars = unify(
            inferred_type,
            current_goal.statement,
            current_goal.context,
            candidate_metavars,
            self.definitions,
        )

        all_potential_goals = subgoals + list(state.goals[1:])
        truly_active_goals = [
            g for g in all_potential_goals if not final_metavars[g.id].is_assigned
        ]
        return ProofState(goals=tuple(truly_active_goals), metavars=final_metavars)

    def change_goal(self, state: ProofState, new_statement: Expr) -> ProofState:
        """ Replace the current goal statement with a definitionally equal statement. """
        state = self.refresh_state(state)
        current_goal = state.current_goal
        if current_goal is None:
            raise KernelStateError("No active goal to change.")

        if not is_def_eq(
            new_statement,
            current_goal.statement,
            current_goal.context,
            state.metavars,
            self.definitions,
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
        self, state: ProofState, hypothesis_name: str, new_type: Expr
    ) -> ProofState:
        """
        Replace the type of a local hypothesis with a definitionally equal type.
        """
        state = self.refresh_state(state)
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
            self.definitions,
        ):
            raise KernelValueError(
                f"change failed: New type for '{hypothesis_name}' is not definitionally equal to the current type."
            )

        updated_local_context = current_goal.local_context | {
            hypothesis_name: new_type
        }
        updated_goal = current_goal.with_context(
            self.global_context | updated_local_context,
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
