"""
Framework-level base class providing method-style tactic access for Theorem and Example.
"""
from __future__ import annotations
from abc import ABC, abstractmethod

from ..ast import Expr, EVar
from ..environment import Environment
from ..kernel import ProofManager, ProofState
from ..tactics import apply, exact, intro, constructor


class ProofScript(ABC):
    """
    Abstract base class for all proof-carrying script objects (Theorem, Example).
    
    This class acts purely as a fluent frontend interface for writing proof scripts. 
    It completely delegates all state mutation and history tracking concerns to ProofManager.
    """

    def __init__(self, statement: Expr, env: Environment):
        self.statement: Expr = statement
        self.env: Environment = env
        self.manager: ProofManager = ProofManager(statement, env)

    @property
    def current_state(self) -> ProofState:
        return self.manager.current_state

    @property
    def is_closed(self) -> bool:
        return self.manager.is_closed

    def undo(self):
        self.manager.undo()

    @abstractmethod
    def qed(self):
        pass

    def intro(self, name: str) -> None:
        intro(self.manager, name)

    def apply(self, expr_or_name: Expr | str) -> None:
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        apply(self.manager, expr)

    def exact(self, expr_or_name: Expr | str) -> None:
        expr = expr_or_name if isinstance(expr_or_name, Expr) else EVar(expr_or_name)
        exact(self.manager, expr)

    def constructor(self) -> None:
        constructor(self.manager)
