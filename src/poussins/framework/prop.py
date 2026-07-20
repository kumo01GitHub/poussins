"""
Prop: public-facing propositional formula DSL.

Wraps the internal Expr AST with Python operator overloads so that
propositions can be written naturally in Python code:

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

from ..ast import (
    Expr, ESort, EVar, EConst, EPi, EApp,
    UnivLevelZero
)


@dataclass(frozen=True)
class Prop:
    expr: Expr

    def __init__(self, expr_or_name: Expr | str) -> None:
        if isinstance(expr_or_name, Expr):
            object.__setattr__(self, "expr", expr_or_name)
        else:
            object.__setattr__(self, "expr", EVar(expr_or_name))

    # ------------------------------------------------------------------
    # Coercion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def to_expr(prop_or_expr: Prop | Expr) -> Expr:
        return prop_or_expr.expr if isinstance(prop_or_expr, Prop) else prop_or_expr

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def prop_sort(cls) -> Prop:
        return cls(ESort(UnivLevelZero()))

    @classmethod
    def top(cls) -> Prop:
        """⊤ (True)."""
        return cls(EConst("True", levels=()))

    @classmethod
    def bot(cls) -> Prop:
        """⊥ (False)."""
        return cls(EConst("False", levels=()))

    # ------------------------------------------------------------------
    # Operator overloads
    # ------------------------------------------------------------------

    def __rshift__(self, other: Prop | Expr) -> Prop:
        """
        P >> Q  →  P → Q  (implication).
        """
        return Prop(EPi(var="_", domain=self.expr, body=self.to_expr(other)))

    def __and__(self, other: Prop | Expr) -> Prop:
        """
        P & Q  →  P ∧ Q  (conjunction).
        """
        return Prop(EApp(EApp(EConst("And", levels=()), self.expr), self.to_expr(other)))

    def __or__(self, other: Prop | Expr) -> Prop:
        """
        P | Q  →  P ∨ Q  (disjunction).
        """
        return Prop(EApp(EApp(EConst("Or", levels=()), self.expr), self.to_expr(other)))

    def __invert__(self) -> Prop:
        """~P  →  P → ⊥  (negation)."""
        return Prop(EPi(var="_", domain=self.expr, body=self.to_expr(self.bot())))

    # ------------------------------------------------------------------
    # Equality / hashing — delegate to Expr
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Prop):
            return self.expr == other.expr
        elif isinstance(other, Expr):
            return self.expr == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.expr)

    def __repr__(self) -> str:
        return f"Prop({self.expr!r})"
