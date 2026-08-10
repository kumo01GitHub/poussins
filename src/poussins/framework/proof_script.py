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
    change,
    constructor, left, right, split,
    cases,
    exfalso,
    induction,
)
from ..utils.logging import getLogger


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
        self.logger = getLogger(__name__)

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
        Introduce a hypothesis with the given name into the local context.
        """
        self._log_before_tactic("intro", [name])
        intro(self.manager, name)
        self._log_after_tactic("intro")

    def intros(self, names: list[str]) -> None:
        """
        Introduce multiple hypotheses into the local context.
        """
        self._log_before_tactic("intros", names)
        intros(self.manager, names)
        self._log_after_tactic("intros")

    def apply(self, expr_or_name: Expr | str) -> None:
        """
        Apply a theorem, hypothesis, or expression to the current goal.
        """
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        self._log_before_tactic("apply", [expr])
        apply(self.manager, expr)
        self._log_after_tactic("apply")

    def exact(self, expr_or_name: Expr | str) -> None:
        """
        Close the current goal with the given expression.
        """
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        self._log_before_tactic("exact", [expr])
        exact(self.manager, expr)
        self._log_after_tactic("exact")

    def change(self, expr_or_name: Expr | str, hypothesis_name: str | None = None) -> None:
        """
        Replace the current goal, or a local hypothesis type, with a definitionally equal expression.
        """
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        self._log_before_tactic("change", [expr, hypothesis_name])
        change(self.manager, expr, hypothesis_name)
        self._log_after_tactic("change")

    def assumption(self) -> None:
        """
        Solve the current goal using a matching hypothesis.
        """
        self._log_before_tactic("assumption")
        assumption(self.manager)
        self._log_after_tactic("assumption")

    def constructor(self, index: int | None = None) -> None:
        """
        Apply an inductive constructor to the current goal.
        """
        self._log_before_tactic("constructor", [index])
        constructor(self.manager, index)
        self._log_after_tactic("constructor")

    def left(self) -> None:
        """
        Select the left branch of a disjunction goal.
        """
        self._log_before_tactic("left")
        left(self.manager)
        self._log_after_tactic("left")

    def right(self) -> None:
        """
        Select the right branch of a disjunction goal.
        """
        self._log_before_tactic("right")
        right(self.manager)
        self._log_after_tactic("right")

    def split(self) -> None:
        """
        Split a conjunction goal into two subgoals.
        """
        self._log_before_tactic("split")
        split(self.manager)
        self._log_after_tactic("split")

    def cases(
        self,
        hypothesis_name: str,
        patterns: tuple[tuple[str, ...], ...] | None = None,
    ) -> None:
        """
        Case-split on an inductive hypothesis.
        """
        self._log_before_tactic("cases", [hypothesis_name, patterns])
        cases(self.manager, hypothesis_name, patterns)
        self._log_after_tactic("cases")

    def exfalso(self) -> None:
        """
        Switch the current goal to False.
        """
        self._log_before_tactic("exfalso")
        exfalso(self.manager)
        self._log_after_tactic("exfalso")

    def induction(self, hypothesis_name: str) -> None:
        """
        Perform induction on a Nat-valued hypothesis.
        """
        self._log_before_tactic("induction", [hypothesis_name])
        induction(self.manager, hypothesis_name)
        self._log_after_tactic("induction")

    def _log_before_tactic(self, tactic_name: str, args: list | None = None) -> None:
        """
        Log the current goal before applying a tactic.
        """
        self.logger.info(f"Executing '{tactic_name}' tactic with: {args}")

    def _log_after_tactic(self, tactic_name: str) -> None:
        """
        Log the current goal after applying a tactic.
        """
        self.logger.info(f"After '{tactic_name}':")
        current_goal = self.current_state.current_goal
        if current_goal is None:
            self.logger.info(f"==> None (proof is closed)")
        else:
            self.logger.info(f"    {current_goal.statement}")
            self.logger.info("-" * 50)
            if current_goal.local_context:
                for name, expr in current_goal.local_context.items():
                    self.logger.info(f"    {name}: {expr}")
