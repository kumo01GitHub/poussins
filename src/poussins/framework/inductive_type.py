"""InductiveType: shared frontend base for inductive-type DSL wrappers."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import ClassVar, override

from ..ast import EApp, EConst, EVar, Expr
from ..environment.library import EqualityDeclaration


@dataclass(frozen=True)
class InductiveType(ABC):
    """Shared immutable wrapper for expressions inhabiting an inductive type.

    Subclasses define ``TYPE_NAME`` and optionally add constructor helpers.
    """

    TYPE_NAME: ClassVar[str] = ""
    EQ_NAME: ClassVar[str] = EqualityDeclaration.EQ_DECLARATION.declaration.name

    expr: Expr

    def __init__(self, expr: Expr | str) -> None:
        """Initialize an inductive type."""
        if isinstance(expr, str):
            expr = EVar(expr)
        object.__setattr__(self, "expr", expr)

    @classmethod
    def type(cls) -> Expr:
        """Return the type expression of the inductive name."""
        return EConst(cls.TYPE_NAME, ())

    @staticmethod
    def to_expr(value: InductiveType | Expr) -> Expr:
        """Return the underlying expression."""
        return value.expr if isinstance(value, InductiveType) else value

    @classmethod
    def eq(cls, left: InductiveType | Expr, right: InductiveType | Expr) -> Expr:
        """Construct an equality proposition over this inductive type."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(EApp(EApp(
            EConst(cls.EQ_NAME, ()), cls.type()), left_expr), right_expr)

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, InductiveType):
            return self.expr == other.expr
        if isinstance(other, Expr):
            return self.expr == other
        return NotImplemented

    @override
    def __hash__(self) -> int:
        return hash(self.expr)

    @override
    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.expr!r})"
