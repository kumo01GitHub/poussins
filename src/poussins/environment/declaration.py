"""
Declaration types stored in the environment.
"""
from __future__ import annotations
from abc import ABC
from dataclasses import dataclass

from ..ast.expr import Expr


class Declaration(ABC):
    """
    Base class for all declarations stored in the environment.
    """
    name: str
    type: Expr


@dataclass(frozen=True)
class ConstantDeclaration(Declaration):
    """
    Global constant information for a definition or theorem.
    """
    name: str
    level_params: tuple[str, ...]
    type: Expr
    value: Expr


@dataclass(frozen=True)
class InductiveDeclaration(Declaration):
    """
    Inductive type information for a data type or logical connective.
    """
    name: str
    level_params: tuple[str, ...]
    type: Expr
    constructor_names: tuple[str, ...]


@dataclass(frozen=True)
class ConstructorDeclaration(Declaration):
    """
    Constructor information for an inductive type.
    """
    name: str
    level_params: tuple[str, ...]
    inductive_name: str
    type: Expr


@dataclass(frozen=True)
class QuotDeclaration(Declaration):
    """
    Quotient type information.
    """
    name: str
    level_params: tuple[str, ...]
    type: Expr
    variant: str
