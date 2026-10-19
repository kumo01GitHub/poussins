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
from typing import ClassVar, cast, override

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

type BindingLike = Sequence[Binding | BindableMixin] | Binding | BindableMixin


@dataclass(frozen=True)
class Prop(BindableMixin):
    """Immutable wrapper for proposition expressions with operator syntax."""

    statement: Expr
    BINDING_LEN: ClassVar[int] = 2

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

    @property
    @override
    def bound_type(self) -> Expr:
        """Return the type of the bound variable (Prop)."""
        return self.type_expr()

    @property
    @override
    def bound_value(self) -> Expr:
        """Return the value of the bound variable (the proposition itself)."""
        return self.statement

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def top(cls) -> Prop:
        """⊤ (True)."""
        return cls(
            EConst(
                name=LogicDeclaration.TRUE_DECLARATION.declaration.name,
                levels=()
            )
        )

    @classmethod
    def bottom(cls) -> Prop:
        """⊥ (False)."""
        return cls(
            EConst(
                name=LogicDeclaration.FALSE_DECLARATION.declaration.name,
                levels=()
            )
        )

    @classmethod
    def _normalize_bindings(cls, bindings: BindingLike) -> Sequence[Binding]:
        def is_binding(obj: object) -> bool:
            return (
                isinstance(obj, tuple)
                and len(obj) == cls.BINDING_LEN
                and isinstance(obj[0], str)
                and isinstance(obj[1], Expr)
            )

        if not bindings:
            raise TypeError("bindings requires at least one binding")

        if is_binding(bindings):
            return (cast(Binding, bindings),)
        elif isinstance(bindings, BindableMixin):
            return (bindings.to_binding(),)
        else:
            normalized: Sequence[Binding] = []
            for binding in bindings:
                if is_binding(binding):
                    normalized.append(cast(Binding, binding))
                elif isinstance(binding, BindableMixin):
                    normalized.append(binding.to_binding())
                else:
                    raise TypeError(
                        "bindings must be a Binding or BindableMixin instance"
                    )

            return normalized

    @classmethod
    def forall(cls, bindings: BindingLike, body: Prop | Expr) -> Prop:
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
    def exists(cls, bindings: BindingLike, body: Prop | Expr) -> Prop:
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
