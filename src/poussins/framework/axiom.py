"""
Axiom: a named proposition accepted without proof.
"""
from __future__ import annotations


class Axiom:
    """A named proposition accepted without proof.

    Axioms always have assurance TRUSTED.

    If *env* is provided the axiom is registered immediately, mirroring
    Coq's ``Axiom foo : T.`` which registers into the global environment
    on the same line.

    Usage::

        # declare and register in one step (Coq-style)
        ax = Axiom("excluded_middle", p | ~p, env)

        # declare only — useful for tests or composing declarations
        ax = Axiom("excluded_middle", p | ~p)
        env.register(ax.to_declaration())
    """
    pass
