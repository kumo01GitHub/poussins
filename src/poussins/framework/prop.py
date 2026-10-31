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

from dataclasses import dataclass
from typing import override

from ..ast import (
    ELam,
    EPi,
    EVar,
    Expr,
    Sort,
    app,
    pi,
)
from ..environment import const
from ..environment.library import AND_IND_SPEC, EXISTS_IND_SPEC, FALSE_IND_SPEC, OR_IND_SPEC, TRUE_IND_SPEC
from .bound_var import BindableMixin, BoundVarLike, normalize_bound_vars
from .environment import STANDARD_ENV


@dataclass(frozen=True)
class Prop(BindableMixin):
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
    def type_ref(cls) -> Expr:
        """Return the type expression of propositions (Prop)."""
        return Sort.PROP.sort

    @property
    def type(self) -> Expr:
        """Return the type expression of this proposition instance."""
        return self.__class__.type_ref()

    @property
    @override
    def bound_type(self) -> Expr:
        """Return the type of the bound variable (Prop)."""
        return self.type_ref()

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
            const(
                env=STANDARD_ENV,
                name=TRUE_IND_SPEC.name,
            )
        )

    @classmethod
    def bottom(cls) -> Prop:
        """⊥ (False)."""
        return cls(
            const(
                env=STANDARD_ENV,
                name=FALSE_IND_SPEC.name,
            )
        )

    @classmethod
    def forall(cls, bound_vars: BoundVarLike, body: Prop | Expr | None) -> Prop:
        """Construct a universal quantifier proposition.

        The interface is intentionally explicit: a tuple of ``(name, type)``
        bound variables and a single body expression. If `body` is omitted (None),
        it defaults to the proposition sort (`Prop`).
        """
        return cls(
            pi(
                normalize_bound_vars(bound_vars),
                cls.to_expr(body if body is not None else Sort.PROP.sort)
            )
        )

    @classmethod
    def exists(cls, bound_vars: BoundVarLike, body: Prop | Expr | None) -> Prop:
        """Construct an existential quantifier proposition.

        Accepts a single Inductive variable, a single (name, type) tuple,
        or a Sequence of bound variables.
        """
        normalized = normalize_bound_vars(bound_vars)
        expr = cls.to_expr(body if body is not None else Sort.PROP.sort)

        for name, type_ in reversed(normalized):
            expr = app(
                const(
                    env=STANDARD_ENV,
                    name=EXISTS_IND_SPEC.name,
                ),
                type_,
                ELam(var=name, domain=type_, body=expr),
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
            app(
                const(
                    env=STANDARD_ENV,
                    name=AND_IND_SPEC.name,
                ),
                self.statement,
                self.to_expr(other)
            )
        )

    def __or__(self, other: Prop | Expr) -> Prop:
        """P | Q  →  P ∨ Q  (disjunction)."""
        return Prop(
            app(
                const(
                    env=STANDARD_ENV,
                    name=OR_IND_SPEC.name,
                ),
                self.statement,
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
