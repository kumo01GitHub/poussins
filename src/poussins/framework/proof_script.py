"""
Framework-level base class providing method-style tactic access for Theorem and Example.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import functools
from typing import Any, Callable

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


def log_tactic(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        self.logger.info(f"Executing '{func.__name__}' tactic with: {args} {kwargs}")

        result = func(self, *args, **kwargs)

        self.logger.info(f"After '{func.__name__}'")
        current_goal = self.current_state.current_goal
        if current_goal is None:
            self.logger.info(f"==> None (proof is closed)")
        else:
            self.logger.info(f"==> Current goal ID: {current_goal.id}")
            self.logger.info(f"    {current_goal.statement}")
            self.logger.info("-" * 50)
            if current_goal.local_context:
                for name, expr in current_goal.local_context.items():
                    self.logger.info(f"    {name}: {expr}")

        return result

    return wrapper


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

    @log_tactic
    def intro(self, name: str) -> None:
        """
        Introduce a hypothesis with the given name into the local context.
        """
        intro(self.manager, name)

    @log_tactic
    def intros(self, names: list[str]) -> None:
        """
        Introduce multiple hypotheses into the local context.
        """
        intros(self.manager, names)

    @log_tactic
    def apply(self, expr_or_name: Expr | str) -> None:
        """
        Apply a theorem, hypothesis, or expression to the current goal.
        """
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        apply(self.manager, expr)

    @log_tactic
    def exact(self, expr_or_name: Expr | str) -> None:
        """
        Close the current goal with the given expression.
        """
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        exact(self.manager, expr)

    @log_tactic
    def change(self, expr_or_name: Expr | str, hypothesis_name: str | None = None) -> None:
        """
        Replace the current goal, or a local hypothesis type, with a definitionally equal expression.
        """
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        change(self.manager, expr, hypothesis_name)

    @log_tactic
    def assumption(self) -> None:
        """
        Solve the current goal using a matching hypothesis.
        """
        assumption(self.manager)

    @log_tactic
    def constructor(self, index: int | None = None) -> None:
        """
        Apply an inductive constructor to the current goal.
        """
        constructor(self.manager, index)

    @log_tactic
    def left(self) -> None:
        """
        Select the left branch of a disjunction goal.
        """
        left(self.manager)

    @log_tactic
    def right(self) -> None:
        """
        Select the right branch of a disjunction goal.
        """
        right(self.manager)

    @log_tactic
    def split(self) -> None:
        """
        Split a conjunction goal into two subgoals.
        """
        split(self.manager)

    @log_tactic
    def cases(
        self,
        hypothesis_name: str,
        patterns: tuple[tuple[str, ...], ...] | None = None,
    ) -> None:
        """
        Case-split on an inductive hypothesis.
        """
        cases(self.manager, hypothesis_name, patterns)

    @log_tactic
    def exfalso(self) -> None:
        """
        Switch the current goal to False.
        """
        exfalso(self.manager)

    @log_tactic
    def induction(self, hypothesis_name: str) -> None:
        """
        Perform induction on a Nat-valued hypothesis.
        """
        induction(self.manager, hypothesis_name)
