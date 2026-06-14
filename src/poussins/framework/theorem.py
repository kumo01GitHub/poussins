"""Theorem, Lemma, Example: proof-carrying DSL objects.

Usage pattern::

    from poussins import Prop, Theorem, Lemma, Axiom, Example, Environment
    from poussins import intro, exact

    p, q = Prop("P"), Prop("Q")
    env = Environment()

    # Theorem: named, registered in Environment
    th = Theorem("identity", p >> p)
    th.intro("h")       # method-style via ProofBase
    th.exact("h")
    th.qed(env)

    # Standalone functions are also available (useful in combinators)
    intro(th.engine, "h")
    exact(th.engine, "h")

    # Lemma: alias for Theorem (stylistic distinction only)
    lem = Lemma("and_comm", (p & q) >> (q & p))
    ...

    # Example: anonymous proof, never registered
    ex = Example(p >> p)
    intro(ex, "h")
    exact(ex, "h")
    assert ex.is_closed

Design:
    Theorem  wraps ProofSession and produces a Declaration on success.
             Inherits ProofDriver for method-style tactic access.
    Example  is like Theorem but anonymous and does not produce a Declaration.

    None of the above hold a reference to an Environment; that is the
    caller's concern.

See also:
    proof_driver.py  for ProofDriver (method delegation layer).
    axiom.py       for Axiom (no-proof declarations).
"""

from __future__ import annotations

from .environment import Environment, Declaration
from .prop import Prop
from .proof_driver import ProofDriver
from ..ast import Formula
from ..errors import FrameworkError


class Theorem(ProofDriver):
    """A named proposition together with an interactive proof session.

    Tactics can be applied as methods (via ProofDriver) or as standalone
    functions — both styles are equivalent::

        th = Theorem("mp", (p >> q) >> p >> q)
        th.intro("hpq")          # method style
        intro(th.engine, "hpq")         # function style — also valid

        th.intro("hp")
        th.apply("hpq")
        th.exact("hp")
        th.qed(env)              # seals the proof and registers into env
    """


    def __init__(
        self,
        name: str,
        statement: Prop
    ) -> None:
        self.name = name
        super().__init__(statement)

    def qed(self, env: Environment):
        if not self.is_closed:
            raise FrameworkError("Not proved.")

        env.add(
            declaration=Declaration(
                name=self.name,
                statement=self.statement,
                assignment=self.assignment,
                assurance=self.assurance
            )
        )
        print(f"Assignment: {self.assignment}")


# Alias for Theorem.
Lemma = Theorem
Proposition = Theorem
Corollary = Theorem
Fact = Theorem
Remark = Theorem
Property = Theorem


class Example(ProofDriver):
    """An anonymous proof for exploration or testing.

    Like Theorem but without a name and without to_declaration().
    Tactics can be applied as methods (via ProofDriver) or as standalone
    functions — both styles are equivalent::

        ex = Example(p >> p)
        ex.intro("h")    # method style
        ex.exact("h")
        assert ex.is_closed
    """
    def __init__(
        self,
        statement: Prop | Formula,
    ) -> None:
        super().__init__(statement)

    def qed(self):
        if not self.is_closed:
            raise FrameworkError("Not proved.")

        print(f"Assignment: {self.assignment}")
