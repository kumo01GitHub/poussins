"""Declaration types stored in the environment."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import override

from ..ast.expr import Expr


@dataclass(frozen=True)
class Declaration(ABC):
    """Base class for all declarations in the environment."""

    name: str
    level_params: tuple[str, ...]
    type: Expr

    @override
    def __str__(self) -> str:
        return f"{self.name} : {self.type}"


@dataclass(frozen=True)
class AxiomDeclaration(Declaration):
    """Axiom declaration."""

    pass


@dataclass(frozen=True)
class DefinitionDeclaration(Declaration):
    """Definition declaration."""

    value: Expr

    @override
    def __str__(self) -> str:
        return f"{self.name} : {self.type} := {self.value}"


@dataclass(frozen=True)
class TheoremDeclaration(Declaration):
    """Theorem declaration."""

    value: Expr

    @override
    def __str__(self) -> str:
        return f"{self.name} : {self.type} := {self.value}"


@dataclass(frozen=True)
class InductiveDeclaration(Declaration):
    """Inductive type information for a data type or logical connective.

    The ``type`` field stores the full type former of the inductive name.

    Examples:
    - ``Nat : Type``
    - ``Eq : Π A : Type, A -> A -> Prop``

    Nullary inductives such as ``Nat`` therefore use a sort as their type
    former, while parameterized inductives use a Pi-shaped expression.

    """

    constructor_names: tuple[str, ...]

    @override
    def __str__(self) -> str:
        constructors = ", ".join(self.constructor_names) if self.constructor_names else "[]"
        return f"{self.name} : {self.type} [{constructors}]"


@dataclass(frozen=True)
class ConstructorDeclaration(Declaration):
    """Constructor information for an inductive type."""

    inductive_name: str

    @override
    def __str__(self) -> str:
        return f"{self.name} : {self.type} (constructor for {self.inductive_name})"


@dataclass(frozen=True)
class RecursorDeclaration(Declaration):
    """Recursor information for an inductive type."""

    inductive_name: str
    num_params: int
    num_indices: int
    num_minors: int

    @override
    def __str__(self) -> str:
        return (
            f"{self.name} : {self.type} "
            f"(recursor for {self.inductive_name}, "
            f"params={self.num_params}, indices={self.num_indices}, minors={self.num_minors})"
        )


@dataclass(frozen=True)
class QuotDeclaration(Declaration):
    """Quotient type information."""

    variant: str

    @override
    def __str__(self) -> str:
        return f"{self.name} : {self.type} (quotient variant={self.variant})"
