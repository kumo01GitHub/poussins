"""
Kernel facade that coordinates proof-state transitions.
"""
from __future__ import annotations
from typing import final

from .proof_engine import ProofEngine
from .proof_session import ProofSession
from .proof_state import ProofState
from .goal import Goal
from .typecheck import instantiate
from ..ast import Expr
from ..environment import Environment


@final
class ProofManager:
    """
    Facade for proof-state operations used by tactics and the DSL.
    """

    def __init__(self, statement: Expr, env: Environment):
        """
        Create a proof manager for a statement in a given environment.
        """
        self.env = env
        self.engine = ProofEngine(env)
        initial_state = self.engine.create_initial_state(statement)
        self.session = ProofSession(initial_state)
        self.root_metavar_id = initial_state.current_goal.id if initial_state.current_goal else None

    @property
    def current_state(self) -> ProofState:
        """
        Return the current proof state (the last state in the history).
        """
        return self.session.current_state

    @property
    def is_closed(self) -> bool:
        """
        Check if the proof session is closed (i.e., no active goals remain).
        """
        return self.session.is_closed

    @property
    def current_proof_term(self) -> Expr:
        """
        Return the current proof term by instantiating the root metavariable with its assignment.
        """
        if self.root_metavar_id is None:
            return None

        metavars = self.current_state.metavars
        root_metavar = metavars.get(self.root_metavar_id)
        if root_metavar is None or root_metavar.assignment is None:
            return None

        return instantiate(root_metavar.assignment, metavars)

    def close_goal(self, assignment: Expr):
        """
        Close the current goal by providing an assignment that satisfies the goal's statement.
        """
        next_state = self.engine.close_goal(self.current_state, assignment)
        self.session.update_state(next_state)

    def refine_goal(self, assignment: Expr, subgoals: list[Goal]):
        """
        Refine the current goal by providing an assignment that splits it into new subgoals.
        """
        next_state = self.engine.refine_goal(self.current_state, assignment, subgoals)
        self.session.update_state(next_state)

    def undo(self) -> None:
        """
        Undo the last proof state, reverting to the previous state in the history stack.
        """
        self.session.undo()
