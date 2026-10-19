"""Public DSL layer: Prop, Axiom, Theorem, Example, and aliases."""
from .axiom import Axiom
from .declaration import (
    declare_axiom,
    declare_definition,
    declare_inductive,
    declare_quot,
    declare_theorem,
)
from .definition import Definition
from .environment import create_environment, create_standard_environment
from .inductive import Inductive
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
from .type import Type

__all__ = [
    # Environment
    "create_environment",
    "create_standard_environment",
    "declare_axiom",
    "declare_definition",
    "declare_theorem",
    "declare_inductive",
    "declare_quot",
    # Axiom
    "Axiom",
    # Definition
    "Definition",
    # Theorem
    "Theorem",
    "Lemma",
    "Proposition",
    "Corollary",
    "Fact",
    "Remark",
    "Property",
    "Example",
    # Inductive
    "Inductive",
    # Expression Wrappers
    "Prop",
    "Type",
]
