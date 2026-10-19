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

Prop is immutable. The underlying Expr is accessible via .statement.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast, override

from ..ast import (
    EApp,
    EConst,
    ELam,
    EPi,
    EVar,
    Expr,
    Sort,
    UnivLevelParam,
)
from ..environment.library import LogicDeclaration
from .bindable_mixin import BindableMixin, Binding

type Boundable = Sequence[Binding | BindableMixin] | Binding | BindableMixin


@dataclass(frozen=True)
class Prop:
    """Immutable wrapper for proposition expressions with operator syntax."""

    statement: Expr

    def __init__(
        self,
        statement: Expr | str,
    ) -> None:
        """Create a proposition from an expression or a named variable."""
        if isinstance(statement, Expr):
            object.__setattr__(self, "statement", statement)
        else:
            object.__setattr__(self, "statement", EVar(statement))

    @staticmethod
    def to_expr(prop_or_expr: Prop | Expr) -> Expr:
        """Return the underlying expression for a proposition-like value."""
        if isinstance(prop_or_expr, Prop):
            return prop_or_expr.statement
        else:
            return prop_or_expr

    @classmethod
    def sort(cls) -> Expr:
        """Return the sort of propositions (Prop)."""
        return Sort.PROP.sort

    @classmethod
    def type_expr(cls) -> Expr:
        """Return the type expression of propositions (Prop)."""
        return cls.sort()

    @property
    def type(self) -> Expr:
        """Return the type expression of this proposition instance."""
        return self.__class__.type_expr()

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def top(cls) -> Prop:
        """⊤ (True)."""
        return cls(EConst(LogicDeclaration.TRUE_DECLARATION.name, levels=()))

    @classmethod
    def bottom(cls) -> Prop:
        """⊥ (False)."""
        return cls(EConst(LogicDeclaration.FALSE_DECLARATION.name, levels=()))

    @staticmethod
    def _normalize_bindings(bindings: Boundable) -> Sequence[Binding]:
        if not bindings:
            raise TypeError("bindings requires at least one binding")

        if isinstance(bindings, Binding.__value__):
            return (cast(Binding, bindings),)
        elif isinstance(bindings, BindableMixin):
            return (bindings.to_binding(),)
        else:
            normalized: Sequence[Binding] = []
            for binding in bindings:
                if isinstance(binding, Binding.__value__):
                    normalized.append(cast(Binding, binding))
                elif isinstance(binding, BindableMixin):
                    normalized.append(binding.to_binding())
                else:
                    raise TypeError(
                        "bindings must be a Binding or BindableMixin instance"
                    )

            return normalized

    @classmethod
    def forall(cls, bindings: Boundable, body: Prop | Expr) -> Prop:
        """Construct a universal quantifier proposition.

        The interface is intentionally explicit: a tuple of ``(name, type)``
        bindings and a single body expression.
        """
        normalized_bindings = cls._normalize_bindings(bindings)
        expr = cls.to_expr(body)

        for name, type_ in reversed(normalized_bindings):
            expr = EPi(name, cls.to_expr(type_), expr)

        return cls(expr)

    @classmethod
    def exists(cls, bindings: Boundable, body: Prop | Expr) -> Prop:
        """Construct an existential quantifier proposition.

        Accepts a single Inductive variable, a single (name, type) tuple,
        or a Sequence of bindings.
        """
        normalized_bindings = cls._normalize_bindings(bindings)
        expr = cls.to_expr(body)

        for name, type_ in reversed(normalized_bindings):
            expr = EApp(
                EApp(
                    EConst(
                        name=LogicDeclaration.EXISTS_DECLARATION.declaration.name,
                        levels=tuple(
                            UnivLevelParam(param) for param in
                            LogicDeclaration.EXISTS_DECLARATION.declaration.level_params
                        )
                    ),
                    type_,
                ),
                ELam(name, type_, expr)
            )

        return cls(expr)

    # ------------------------------------------------------------------
    # Operator overloads
    # ------------------------------------------------------------------

    def __rshift__(self, other: Prop | Expr) -> Prop:
        """P >> Q  →  P → Q  (implication)."""
        return Prop(EPi(var="_", domain=self.statement, body=self.to_expr(other)))

    def __and__(self, other: Prop | Expr) -> Prop:
        """P & Q  →  P ∧ Q  (conjunction)."""
        return Prop(
            EApp(EApp(EConst("And", levels=()), self.statement), self.to_expr(other))
        )

    def __or__(self, other: Prop | Expr) -> Prop:
        """P | Q  →  P ∨ Q  (disjunction)."""
        return Prop(
            EApp(
                EApp(EConst("Or", levels=()), self.statement),
                self.to_expr(other)
            )
        )

    def __invert__(self) -> Prop:
        """~P  →  P → ⊥  (negation)."""
        return Prop(
            EPi(
                var="_",
                domain=self.statement,
                body=self.to_expr(self.bottom())
            )
        )

    # ------------------------------------------------------------------
    # Equality / hashing — delegate to Expr
    # ------------------------------------------------------------------

    @override
    def __eq__(self, other: object) -> bool:
        """Compare propositions by their underlying expression."""
        if isinstance(other, Prop):
            return self.statement == other.statement
        elif isinstance(other, Expr):
            return self.statement == other
        return NotImplemented

    @override
    def __hash__(self) -> int:
        """Hash the wrapped expression."""
        return hash(self.statement)

    @override
    def __repr__(self) -> str:
        """Return a debug representation of the proposition."""
        return f"Prop({self.statement!r})"
