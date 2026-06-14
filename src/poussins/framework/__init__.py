"""
Public DSL layer: Prop, Axiom, Theorem, Example, and aliases.
"""

from .prop import Prop
from .axiom import Axiom
from .theorem import (
    Theorem,
    Lemma,
    Proposition,
    Corollary,
    Fact,
    Remark,
    Property,
    Example,
)

__all__ = [
    "Prop",
    "Axiom",
    "Theorem",
    "Lemma",
    "Proposition",
    "Corollary",
    "Fact",
    "Remark",
    "Property",
    "Example",
]
