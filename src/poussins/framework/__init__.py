"""Public DSL layer: Prop, Axiom, Theorem, Example, and aliases."""
from .axiom import Axiom
from .declaration import (
    declare_axiom,
    declare_definition,
    declare_inductive,
    declare_quot,
    declare_theorem,
)
from .environment import create_environment, create_standard_environment
from .prop import Prop
from .theorem import (
    Corollary,
    Example,
    Fact,
    Lemma,
    Property,
    Proposition,
    Remark,
    Theorem,
)

__all__ = [
    "Axiom",
    "Corollary",
    "Example",
    "Fact",
    "Lemma",
    "Prop",
    "Property",
    "Proposition",
    "Remark",
    "Theorem",
    "create_environment",
    "create_standard_environment",
    "declare_axiom",
    "declare_definition",
    "declare_inductive",
    "declare_theorem",
    "declare_quot",
]
