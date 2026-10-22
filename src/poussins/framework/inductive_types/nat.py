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

    def __init__(self, value: int | Expr | str) -> None:
        """Initialize a natural number."""
        if isinstance(value, int):
            if value < 0:
                raise ValueError("Natural numbers must be non-negative.")
            expr: Expr = Nat.zero().value
            for _ in range(value):
                expr = Nat.succ(expr).value
            value = expr

        super().__init__(value)

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

    @classmethod
    def sub(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.sub n m."""
        return cls(
            EApp(
                EApp(
                    EConst(
                        name=NatDeclaration.NAT_SUB_DECLARATION.declaration.name,
                        levels=cls.levels(),
                    ),
                    cls.to_expr(n),
                ),
                cls.to_expr(m),
            )
        )

    @classmethod
    def mul(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.mul n m."""
        return cls(
            EApp(
                EApp(
                    EConst(
                        name=NatDeclaration.NAT_MUL_DECLARATION.declaration.name,
                        levels=cls.levels(),
                    ),
                    cls.to_expr(n),
                ),
                cls.to_expr(m),
            )
        )

    @classmethod
    def div(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.div n m."""
        return cls(
            EApp(
                EApp(
                    EConst(
                        name=NatDeclaration.NAT_DIV_DECLARATION.declaration.name,
                        levels=cls.levels(),
                    ),
                    cls.to_expr(n),
                ),
                cls.to_expr(m),
            )
        )

    @classmethod
    def mod(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.mod n m."""
        return cls(
            EApp(
                EApp(
                    EConst(
                        name=NatDeclaration.NAT_MOD_DECLARATION.declaration.name,
                        levels=cls.levels(),
                    ),
                    cls.to_expr(n),
                ),
                cls.to_expr(m),
            )
        )

    def __add__(self, other: Nat | Expr) -> Nat:
        """Allow `n + m` syntax in Python DSL."""
        return Nat.add(self, other)

    def __sub__(self, other: Nat | Expr) -> Nat:
        """Allow `n - m` syntax in Python DSL."""
        return Nat.sub(self, other)

    def __mul__(self, other: Nat | Expr) -> Nat:
        """Allow `n * m` syntax in Python DSL."""
        return Nat.mul(self, other)

    def __truediv__(self, other: Nat | Expr) -> Nat:
        """Allow `n / m` syntax in Python DSL."""
        return Nat.div(self, other)

    def __floordiv__(self, other: Nat | Expr) -> Nat:
        """Allow `n // m` syntax in Python DSL."""
        return Nat.div(self, other)

    def __mod__(self, other: Nat | Expr) -> Nat:
        """Allow `n % m` syntax in Python DSL."""
        return Nat.mod(self, other)
