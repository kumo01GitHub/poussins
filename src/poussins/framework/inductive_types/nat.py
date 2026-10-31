"""Nat: public-facing natural number DSL.

This wraps the internal Expr AST for natural numbers so proofs can be written
in a more ergonomic way.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...ast import Expr, app
from ...environment import const
from ...environment.library import (
    NAT_ADD_DEF_SPEC,
    NAT_DIV_DEF_SPEC,
    NAT_IND_SPEC,
    NAT_MOD_DEF_SPEC,
    NAT_MUL_DEF_SPEC,
    NAT_SUB_DEF_SPEC,
)
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=NAT_IND_SPEC)
class Nat(Inductive):
    """Immutable wrapper for natural number expressions."""

    ZERO_IDX: ClassVar[int] = 0
    SUCC_IDX: ClassVar[int] = 1

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
        env = cls.env()
        return cls(
            const(
                env=env if env is not None else STANDARD_ENV,
                name=NAT_IND_SPEC.constructors[cls.ZERO_IDX][0],
            )
        )

    @classmethod
    def succ(cls, n: Nat | Expr) -> Nat:
        """Construct the successor of a natural number."""
        env = cls.env()
        return cls(
            app(
                const(
                    env=env if env is not None else STANDARD_ENV,
                    name=NAT_IND_SPEC.constructors[cls.SUCC_IDX][0],
                ),
                cls.to_expr(n)
            )
        )

    @classmethod
    def add(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.add n m."""
        env = cls.env()
        return cls(
            app(
                const(
                    env=env if env is not None else STANDARD_ENV,
                    name=NAT_ADD_DEF_SPEC.name,
                ),
                cls.to_expr(n),
                cls.to_expr(m),
            )
        )

    @classmethod
    def sub(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.sub n m."""
        env = cls.env()
        return cls(
            app(
                const(
                    env=env if env is not None else STANDARD_ENV,
                    name=NAT_SUB_DEF_SPEC.name,
                ),
                cls.to_expr(n),
                cls.to_expr(m),
            )
        )

    @classmethod
    def mul(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.mul n m."""
        env = cls.env()
        return cls(
            app(
                const(
                    env=env if env is not None else STANDARD_ENV,
                    name=NAT_MUL_DEF_SPEC.name,
                ),
                cls.to_expr(n),
                cls.to_expr(m),
            )
        )

    @classmethod
    def div(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.div n m."""
        env = cls.env()
        return cls(
            app(
                const(
                    env=env if env is not None else STANDARD_ENV,
                    name=NAT_DIV_DEF_SPEC.name,
                ),
                cls.to_expr(n),
                cls.to_expr(m),
            )
        )

    @classmethod
    def mod(cls, n: Nat | Expr, m: Nat | Expr) -> Nat:
        """Construct Nat.mod n m."""
        env = cls.env()
        return cls(
            app(
                const(
                    env=env if env is not None else STANDARD_ENV,
                    name=NAT_MOD_DEF_SPEC.name,
                ),
                cls.to_expr(n),
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
