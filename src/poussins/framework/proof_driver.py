"""
ProofDriver: tactic methods for proof-carrying DSL objects (Theorem, Example).

This abstract base class provides method-style tactic access on top of the underlying
ProofEngine. The logic of each tactic lives in ``tactics/primitive.py``
and ``tactics/derived.py``; this module only delegates to those functions.

Classes that inherit ProofDriver must implement the ``engine`` property.

Usage::

    th = Theorem("identity", p >> p)
    th.intro("h")
    th.exact("h")
    th.qed(env)

Alternatively, the same tactics are still available as standalone
functions for use in combinators or batch execution::

    from poussins import intro, exact
    intro(th.engine, "h")
    exact(th.engine, "h")
"""
from __future__ import annotations
from abc import ABC

from .prop import Prop
from ..ast import Formula, ProofTerm
from ..kernel import ProofAssurance, ProofEngine
from ..tactics import intro, exact, apply, intros, assumption


class ProofDriver(ABC):
    def __init__(self, statement: Prop | Formula):
        self.__setattr__("engine", ProofEngine(Prop.to_formula(statement)))

    @property
    def is_closed(self) -> bool:
        return self.engine.is_closed

    @property
    def statement(self) -> Formula:
        return self.engine.goal.formula

    @property
    def assignment(self) -> ProofTerm:
        return self.engine.goal.assignment

    @property
    def assurance(self) -> ProofAssurance:
        return self.engine.goal.assurance

    # ------------------------------------------------------------------
    # Primitive tactics
    # ------------------------------------------------------------------

    def intro(self, name: str) -> None:
        intro(self.engine, name)

    def exact(self, term_or_hyp: ProofTerm | str) -> None:
        exact(self.engine, term_or_hyp)

    def apply(self, term_or_hyp: ProofTerm | str) -> None:
        apply(self.engine, term_or_hyp)

    # ------------------------------------------------------------------
    # Derived tactics
    # ------------------------------------------------------------------

    def intros(self, hyp_names: list[str]) -> None:
        intros(self.engine, hyp_names)

    def assumption(self) -> None:
        assumption(self.engine)
