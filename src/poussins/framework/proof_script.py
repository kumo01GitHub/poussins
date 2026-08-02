"""
Framework-level base class providing method-style tactic access for Theorem and Example.
"""
from __future__ import annotations
from abc import ABC, abstractmethod

from ..ast import Expr, EVar
from ..environment import Environment
from ..kernel import ProofManager, ProofState
from ..tactics import (
    apply,
    exact, assumption,
    intro, intros,
    constructor, left, right, split,
    cases,
    exfalso,
    induction,
)


class ProofScript(ABC):
    """
    Abstract base class for all proof-carrying script objects (Theorem, Example).

    This class acts purely as a fluent frontend interface for writing proof scripts.
    It completely delegates all state mutation and history tracking concerns to ProofManager.
    """

    def __init__(self, statement: Expr, env: Environment):
        """
        Create a proof script bound to a statement and environment.
        """
        self.statement: Expr = statement
        self.env: Environment = env
        self.manager: ProofManager = ProofManager(statement, env)

    @property
    def current_state(self) -> ProofState:
        """
        Return the current proof state.
        """
        return self.manager.current_state

    @property
    def is_closed(self) -> bool:
        """
        Return whether the proof has no remaining goals.
        """
        return self.manager.is_closed

    def undo(self):
        """
        Revert the proof to the previous state.
        """
        self.manager.undo()

    @abstractmethod
    def qed(self):
        """
        Finalize the proof script.
        """
        pass

    def intro(self, name: str) -> None:
        """
        Introduce one local variable.
        """
        intro(self.manager, name)

    def intros(self, names: list[str]) -> None:
        """
        Introduce multiple local variables.
        """
        intros(self.manager, names)

    def apply(self, expr_or_name: Expr | str) -> None:
        """
        Apply a theorem, hypothesis, or expression to the current goal.
        """
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        apply(self.manager, expr)

    def exact(self, expr_or_name: Expr | str) -> None:
        """
        Close the current goal with the given expression.
        """
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        exact(self.manager, expr)

    def assumption(self) -> None:
        """
        Solve the current goal using a matching hypothesis.
        """
        assumption(self.manager)

    def constructor(self, index: int | None = None) -> None:
        """
        Apply an inductive constructor to the current goal.
        """
        constructor(self.manager, index)

    def left(self) -> None:
        """
        Select the left branch of a disjunction goal.
        """
        left(self.manager)

    def right(self) -> None:
        """
        Select the right branch of a disjunction goal.
        """
        right(self.manager)

    def split(self) -> None:
        """
        Split a conjunction goal into two subgoals.
        """
        split(self.manager)

    def cases(
        self,
        hypothesis_name: str,
        patterns: tuple[tuple[str, ...], ...] | None = None,
    ) -> None:
        """
        Case-split on an inductive hypothesis.
        """
        cases(self.manager, hypothesis_name, patterns)

    def exfalso(self) -> None:
        """
        Switch the current goal to False.
        """
        exfalso(self.manager)

    def induction(self, hypothesis_name: str) -> None:
        """
        Perform induction on a Nat-valued hypothesis.
        """
        induction(self.manager, hypothesis_name)
