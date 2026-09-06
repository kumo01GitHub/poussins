"""Prop: public-facing propositional formula DSL.

Wraps the internal Expr AST with Python operator overloads so that propositions
can be written naturally in Python code:

    p, q, r = Prop("P"), Prop("Q"), Prop("R")
    p >> (q >> r)  # P → (Q → R)  (implication)
    p & q          # P ∧ Q        (conjunction)
    p | q          # P ∨ Q        (disjunction)
    ~p             # ¬P           (negation, sugar for P → ⊥)
    Prop.top()     # ⊤            (True)
    Prop.bot()     # ⊥            (False)

Prop is immutable. The underlying Expr is accessible via .expr.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ..ast import (
    EApp,
    EConst,
    EPi,
    EVar,
    Expr,
)
from ..environment import DefinitionDeclaration, Environment
from ..environment.library import Sort

Binding = tuple[str, Expr]


@dataclass(frozen=True)
class Prop:
    """Immutable wrapper for proposition expressions with operator syntax."""

    expr: Expr

    def __init__(
        self,
        expr_or_name: Expr | str,
        env: Environment | None = None
    ) -> None:
        """Create a proposition from an expression or a named variable."""
        if isinstance(expr_or_name, Expr):
            object.__setattr__(self, "expr", expr_or_name)
        else:
            object.__setattr__(self, "expr", EVar(expr_or_name))
            if env is not None and env.get(expr_or_name) is None:
                env.add(
                    DefinitionDeclaration(
                        name=expr_or_name,
                        level_params=(),
                        type=Sort.PROP.sort,
                        value=EConst("P", ()),
                    )
                )

    # ------------------------------------------------------------------
    # Coercion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def to_expr(prop_or_expr: Prop | Expr) -> Expr:
        """Return the underlying expression for a proposition-like value."""
        if isinstance(prop_or_expr, Prop):
            return prop_or_expr.expr
        else:
            return prop_or_expr

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def top(cls) -> Prop:
        """⊤ (True)."""
        return cls(EConst("True", levels=()))

    @classmethod
    def bottom(cls) -> Prop:
        """⊥ (False)."""
        return cls(EConst("False", levels=()))

    @classmethod
    def forall(cls, bindings: tuple[Binding, ...], body: Prop | Expr) -> Prop:
        """Construct a universal quantifier proposition.

        The interface is intentionally explicit: a tuple of ``(name, type)``
        bindings and a single body expression.
        """
        if not bindings:
            raise TypeError("forall() requires at least one binding")
        if not isinstance(body, (Expr, Prop)):
            raise TypeError("forall() missing required body argument")

        expr = cls.to_expr(body)
        for name, typ in reversed(tuple(bindings)):
            if not isinstance(name, str):
                raise TypeError("each binding name must be a string")
            if not isinstance(typ, (Expr, Prop)):
                raise TypeError("each binding type must be an Expr or Prop")
            expr = EPi(name, cls.to_expr(typ), expr)
        return cls(expr)

    @classmethod
    def exists(cls, bindings: tuple[Binding, ...], body: Prop | Expr) -> Prop:
        """Construct an existential quantifier proposition.

        The interface is intentionally explicit: a tuple of ``(name, type)``
        bindings and a single body expression.
        """
        if not bindings:
            raise TypeError("exists() requires at least one binding")
        if not isinstance(body, (Expr, Prop)):
            raise TypeError("exists() missing required body argument")

        expr = cls.to_expr(body)
        for name, typ in reversed(tuple(bindings)):
            if not isinstance(name, str):
                raise TypeError("each binding name must be a string")
            if not isinstance(typ, (Expr, Prop)):
                raise TypeError("each binding type must be an Expr or Prop")
            expr = EPi(name, cls.to_expr(typ), expr)
        return cls(expr)

    # ------------------------------------------------------------------
    # Operator overloads
    # ------------------------------------------------------------------

    def __rshift__(self, other: Prop | Expr) -> Prop:
        """P >> Q  →  P → Q  (implication)."""
        return Prop(EPi(var="_", domain=self.expr, body=self.to_expr(other)))

    def __and__(self, other: Prop | Expr) -> Prop:
        """P & Q  →  P ∧ Q  (conjunction)."""
        return Prop(
            EApp(EApp(EConst("And", levels=()), self.expr), self.to_expr(other))
        )

    def __or__(self, other: Prop | Expr) -> Prop:
        """P | Q  →  P ∨ Q  (disjunction)."""
        return Prop(EApp(EApp(EConst("Or", levels=()), self.expr), self.to_expr(other)))

    def __invert__(self) -> Prop:
        """~P  →  P → ⊥  (negation)."""
        return Prop(EPi(var="_", domain=self.expr, body=self.to_expr(self.bottom())))

    # ------------------------------------------------------------------
    # Equality / hashing — delegate to Expr
    # ------------------------------------------------------------------

    @override
    def __eq__(self, other: object) -> bool:
        """Compare propositions by their underlying expression."""
        if isinstance(other, Prop):
            return self.expr == other.expr
        elif isinstance(other, Expr):
            return self.expr == other
        return NotImplemented

    @override
    def __hash__(self) -> int:
        """Hash the wrapped expression."""
        return hash(self.expr)

    @override
    def __repr__(self) -> str:
        """Return a debug representation of the proposition."""
        return f"Prop({self.expr!r})"
