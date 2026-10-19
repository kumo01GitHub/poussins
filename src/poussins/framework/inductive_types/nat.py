"""Nat: public-facing natural number DSL.

This wraps the internal Expr AST for natural numbers so proofs can be written
in a more ergonomic way.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...ast import EApp, EConst, Expr
from ...environment.library import NatDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Nat(Inductive):
    """Immutable wrapper for natural number expressions."""

    TYPE_NAME: ClassVar[str] = NatDeclaration.NAT_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        NatDeclaration.NAT_DECLARATION.declaration.level_params
    )

    @classmethod
    def zero(cls) -> Nat:
        """Construct zero."""
        return cls(
            EConst(
                NatDeclaration.NAT_ZERO_DECLARATION.declaration.name,
                levels=cls.levels()
            )
        )

    @classmethod
    def succ(cls, n: Nat | Expr) -> Nat:
        """Construct the successor of a natural number."""
        return cls(
            EApp(
                EConst(
                    NatDeclaration.NAT_SUCC_DECLARATION.declaration.name,
                    levels=cls.levels()
                ),
                cls.to_expr(n)
            )
        )

    @classmethod
    def add(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.add n m."""
        return cls(
            EApp(
                EApp(
                    EConst(
                        name=NatDeclaration.NAT_ADD_DECLARATION.declaration.name,
                        levels=cls.levels(),
                    ),
                    cls.to_expr(n)
                ),
                cls.to_expr(m)
            )
        )

    def __add__(self, other: Nat | Expr) -> Nat:
        """Allow `n + m` syntax in Python DSL."""
        return Nat.add(self, other)
