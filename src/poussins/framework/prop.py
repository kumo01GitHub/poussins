"""
Prop: public-facing propositional formula DSL.
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
    Expr,
    EVar,
    EConst,
    EPi,
    EApp,
)
from ..environment import Environment, DefinitionDeclaration
from ..environment.library import Sort


@dataclass(frozen=True)
class Prop:
    """
    Immutable wrapper for proposition expressions with operator syntax.
    """

    expr: Expr

    def __init__(self, expr_or_name: Expr | str, env: Environment | None = None) -> None:
        """
        Create a proposition from an expression or a named variable.
        """
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
    def to_expr(prop_or_expr: Prop | Expr | object) -> Expr:
        """
        Return the underlying expression for a proposition-like value.
        """
        if isinstance(prop_or_expr, Prop):
            return prop_or_expr.expr
        if isinstance(prop_or_expr, Expr):
            return prop_or_expr
        if hasattr(prop_or_expr, "expr") and isinstance(getattr(prop_or_expr, "expr"), Expr):
            return prop_or_expr.expr
        if hasattr(prop_or_expr, "to_expr") and callable(getattr(prop_or_expr, "to_expr")):
            coerced = prop_or_expr.to_expr(prop_or_expr)
            if isinstance(coerced, Expr):
                return coerced
        return prop_or_expr

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def top(cls) -> Prop:
        """
        ⊤ (True).
        """
        return cls(EConst("True", levels=()))

    @classmethod
    def bottom(cls) -> Prop:
        """
        ⊥ (False).
        """
        return cls(EConst("False", levels=()))

    @classmethod
    def forall(cls, *bindings: object) -> Prop:
        """Construct a universal quantifier proposition."""
        if len(bindings) < 2:
            raise TypeError("forall() requires at least one binding and a body")

        body = bindings[-1]
        binding_args = bindings[:-1]

        if not isinstance(body, (Expr, Prop)) and not hasattr(body, "expr"):
            raise TypeError("forall() missing required body argument")

        if len(binding_args) == 1 and isinstance(binding_args[0], (list, tuple)) and len(binding_args[0]) > 0 and isinstance(binding_args[0][0], (list, tuple)):
            expr = cls.to_expr(body)
            for binding in reversed(list(binding_args[0])):
                if not isinstance(binding, (list, tuple)) or len(binding) != 2:
                    raise TypeError("each binding must be a (name, type) pair")
                name, typ = binding
                expr = EPi(name, cls.to_expr(typ), expr)
            return cls(expr)

        if len(binding_args) == 1 and isinstance(binding_args[0], (list, tuple)) and len(binding_args[0]) > 0 and isinstance(binding_args[0][0], str):
            name, typ = binding_args[0]
            return cls(EPi(name, cls.to_expr(typ), cls.to_expr(body)))

        if len(binding_args) >= 2 and isinstance(binding_args[0], str):
            var_name, domain = binding_args[0], binding_args[1]
            expr = cls.to_expr(body)
            for name, typ in reversed(list(binding_args[2:])):
                expr = EPi(name, cls.to_expr(typ), expr)
            return cls(EPi(var_name, cls.to_expr(domain), expr))

        if len(binding_args) >= 1 and isinstance(binding_args[0], (list, tuple)):
            expr = cls.to_expr(body)
            for binding in reversed(list(binding_args)):
                if not isinstance(binding, (list, tuple)) or len(binding) != 2:
                    raise TypeError("each binding must be a (name, type) pair")
                name, typ = binding
                expr = EPi(name, cls.to_expr(typ), expr)
            return cls(expr)

        raise TypeError("forall() expects a binding or a sequence of (name, type) pairs")

    @classmethod
    def exists(cls, *bindings: object) -> Prop:
        """Construct an existential quantifier proposition."""
        if len(bindings) < 2:
            raise TypeError("exists() requires at least one binding and a body")

        body = bindings[-1]
        binding_args = bindings[:-1]

        if not isinstance(body, (Expr, Prop)) and not hasattr(body, "expr"):
            raise TypeError("exists() missing required body argument")

        if len(binding_args) == 1 and isinstance(binding_args[0], (list, tuple)) and len(binding_args[0]) > 0 and isinstance(binding_args[0][0], (list, tuple)):
            expr = cls.to_expr(body)
            for binding in reversed(list(binding_args[0])):
                if not isinstance(binding, (list, tuple)) or len(binding) != 2:
                    raise TypeError("each binding must be a (name, type) pair")
                name, typ = binding
                expr = EPi(name, cls.to_expr(typ), expr)
            return cls(expr)

        if len(binding_args) >= 2 and isinstance(binding_args[0], str):
            var_name, domain = binding_args[0], binding_args[1]
            expr = cls.to_expr(body)
            for name, typ in reversed(list(binding_args[2:])):
                expr = EPi(name, cls.to_expr(typ), expr)
            return cls(EPi(var_name, cls.to_expr(domain), expr))

        if len(binding_args) >= 1 and isinstance(binding_args[0], (list, tuple)):
            expr = cls.to_expr(body)
            for binding_group in reversed(binding_args):
                if not isinstance(binding_group, (list, tuple)):
                    raise TypeError("each binding must be a (name, type) pair")
                for binding in reversed(list(binding_group)):
                    if not isinstance(binding, (list, tuple)) or len(binding) != 2:
                        raise TypeError("each binding must be a (name, type) pair")
                    name, typ = binding
                    expr = EPi(name, cls.to_expr(typ), expr)
            return cls(expr)

        raise TypeError("exists() expects a binding or a sequence of (name, type) pairs")

    # ------------------------------------------------------------------
    # Operator overloads
    # ------------------------------------------------------------------

    def __rshift__(self, other: Prop | Expr) -> Prop:
        """ P >> Q  →  P → Q  (implication). """
        return Prop(EPi(var="_", domain=self.expr, body=self.to_expr(other)))

    def __and__(self, other: Prop | Expr) -> Prop:
        """ P & Q  →  P ∧ Q  (conjunction). """
        return Prop(EApp(EApp(EConst("And", levels=()), self.expr), self.to_expr(other)))

    def __or__(self, other: Prop | Expr) -> Prop:
        """ P | Q  →  P ∨ Q  (disjunction). """
        return Prop(EApp(EApp(EConst("Or", levels=()), self.expr), self.to_expr(other)))

    def __invert__(self) -> Prop:
        """ ~P  →  P → ⊥  (negation). """
        return Prop(EPi(var="_", domain=self.expr, body=self.to_expr(self.bottom())))

    # ------------------------------------------------------------------
    # Equality / hashing — delegate to Expr
    # ------------------------------------------------------------------

    @override
    def __eq__(self, other: object) -> bool:
        """
        Compare propositions by their underlying expression.
        """
        if isinstance(other, Prop):
            return self.expr == other.expr
        elif isinstance(other, Expr):
            return self.expr == other
        return NotImplemented

    @override
    def __hash__(self) -> int:
        """
        Hash the wrapped expression.
        """
        return hash(self.expr)

    @override
    def __repr__(self) -> str:
        """
        Return a debug representation of the proposition.
        """
        return f"Prop({self.expr!r})"
