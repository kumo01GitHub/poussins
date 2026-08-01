from __future__ import annotations
from abc import ABC
from dataclasses import dataclass

from ..ast.expr import Expr



class Declaration(ABC):
    """
    Base class for all declarations in the environment.
    """
    name: str
    type: Expr


@dataclass(frozen=True)
class ConstantDeclaration(Declaration):
    """
    Global constant information (def / theorem).
    """
    name: str
    level_params: tuple[str, ...]
    type: Expr
    value: Expr


@dataclass(frozen=True)
class InductiveDeclaration(Declaration):
    """
    Inductive type information (data type / logical connective).
    """
    name: str
    level_params: tuple[str, ...]
    type: Expr
    constructor_names: tuple[str, ...]


@dataclass(frozen=True)
class ConstructorDeclaration(Declaration):
    """Constructor information belonging to an inductive type (Nat.zero, And.intro)."""
    name: str
    level_params: tuple[str, ...]
    inductive_name: str
    type: Expr


@dataclass(frozen=True)
class QuotDeclaration(Declaration):
    """
    Quotient type information (Quot, Quot.mk, Quot.lift, Quot.sound).
    """
    name: str
    level_params: tuple[str, ...]
    type: Expr
    variant: str
