"""DeclaredType: shared frontend base for declaration-backed DSL wrappers."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import ClassVar, override

from ..ast import EApp, EConst, EVar, Expr
from ..environment.library import EqualityDeclaration


@dataclass(frozen=True)
class DeclaredType(ABC):
    """Shared immutable wrapper for expressions backed by declarations."""

    TYPE_NAME: ClassVar[str] = ""
    EQ_NAME: ClassVar[str] = EqualityDeclaration.EQ_DECLARATION.declaration.name
    EQ_ARITY: ClassVar[int] = 2

    expr: Expr

    def __init__(self, expr: Expr | str) -> None:
        """Initialize a declaration-backed wrapper."""
        if isinstance(expr, str):
            expr = EVar(expr)
        object.__setattr__(self, "expr", expr)

    @classmethod
    def type(cls, *args: DeclaredType | Expr) -> Expr:
        """Return the declaration type applied to zero or more arguments."""
        result: Expr = EConst(cls.TYPE_NAME, ())
        for arg in args:
            result = EApp(result, cls.to_expr(arg))
        return result

    @staticmethod
    def to_expr(value: DeclaredType | Expr) -> Expr:
        """Return the underlying expression."""
        return value.expr if isinstance(value, DeclaredType) else value

    @classmethod
    def eq(cls, *args: DeclaredType | Expr) -> Expr:
        """Construct an equality proposition over this declaration-backed type."""
        if len(args) != cls.EQ_ARITY:
            raise TypeError(
                f"{cls.__name__}.eq expects {cls.EQ_ARITY} arguments, got {len(args)}"
            )
        left, right = args
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type()), left_expr),
            right_expr,
        )

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, DeclaredType):
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
