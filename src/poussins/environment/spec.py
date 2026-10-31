"""Specifications for axioms, definitions, theorems, and inductive types in the environment."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..ast import Expr


@dataclass(frozen=True)
class AxiomSpec:
    """Specification for an axiom in the environment."""

    name: str
    statement: Expr


@dataclass(frozen=True)
class DefinitionSpec:
    """Specification for a definition in the environment."""

    name: str
    type: Expr
    value: Expr


@dataclass(frozen=True)
class TheoremSpec:
    """Specification for a theorem in the environment."""

    name: str
    statement: Expr
    term: Expr


@dataclass(frozen=True)
class InductiveSpec:
    """Specification for an inductive type in the environment."""

    name: str
    type: Expr
    constructors: Sequence[tuple[str, Expr]]
