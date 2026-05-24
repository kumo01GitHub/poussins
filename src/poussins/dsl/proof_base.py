"""ProofBase: tactic methods for proof-carrying DSL objects (Theorem, Example).

This abstract base class provides method-style tactic access on top of the underlying
ProofEngine. The logic of each tactic lives in ``tactics/primitive.py``
and ``tactics/derived.py``; this module only delegates to those functions.

Classes that inherit ProofBase must implement the ``engine`` property.

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

from ..ast.formulas import Formula
from ..ast.proof_terms import ProofTerm
from ..kernel.proof_engine import ProofEngine
from .prop import Prop


class ProofBase(ABC):
    def __init__(self, statement: Prop | Formula):
        self.__setattr__("engine", ProofEngine(Prop.to_formula(statement)))

    def is_closed(self) -> bool:
        return self.engine.is_closed()

    def qed(self):
        # TODO: Add to Envirnonment and closed status should be checked in engine.
        if not self.is_closed():
            raise ValueError("Not proofed.")
        print(f"Assignment: {self.engine.goal.assignment}")

    # ------------------------------------------------------------------
    # Primitive tactics
    # ------------------------------------------------------------------

    def intro(self, name: str) -> None:
        from ..tactics.primitive import intro
        intro(self.engine, name)

    def exact(self, term_or_hyp: ProofTerm | str) -> None:
        from ..tactics.primitive import exact
        exact(self.engine, term_or_hyp)

    def apply(self, term_or_hyp: ProofTerm | str) -> None:
        from ..tactics.primitive import apply
        apply(self.engine, term_or_hyp)

    # ------------------------------------------------------------------
    # Derived tactics
    # ------------------------------------------------------------------

    # TODO: add derived tactics here
