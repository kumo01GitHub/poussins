"""
Prop: public-facing proposition DSL.

Wraps the internal Expr AST with Python operator overloads so that
propositions can be written naturally in Python code:

    p, q = Prop("P"), Prop("Q")
    p >> q        # P → Q  (implication)
    p & q         # P ∧ Q  (conjunction)
    p | q         # P ∨ Q  (disjunction)
    ~p            # ¬P     (negation, sugar for P → ⊥)
    Prop.top()    # ⊤
    Prop.bot()    # ⊥
    nat = Prop.sort("Nat")
    Prop.exists("x", nat, p.expr)  # ∃x:Nat. P
    Prop.forall("x", nat, p.expr)  # ∀x:Nat. P
    Prop.eq(Prop.var("x"), Prop.var("x"))
    Prop.pred("lt", Prop.var("x"), Prop.nat(3))

Prop is immutable.  The underlying Expr is accessible via .expr.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..ast import (
    Sort,
    Expr,
    EVar,
    EConst,
    EApp,
    ENat,
    EPropVar,
    EPred,
    EEq,
    ETop,
    EBot,
    EForall,
    EExists,
    EAnd,
    EImp,
    EOr,
)


@dataclass(frozen=True)
class Prop:
    def __init__(self, expr: Expr | str) -> None:
        if isinstance(expr, Expr):
            object.__setattr__(self, "expr", expr)
        else:
            object.__setattr__(self, "expr", EPropVar(expr))

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def top(cls) -> Prop:
        """⊤ (True)."""
        return cls(ETop())

    @classmethod
    def bot(cls) -> Prop:
        """⊥ (False)."""
        return cls(EBot())

    @classmethod
    def exists(cls, var: str, sort: Sort, body: Expr) -> Prop:
        """∃var:sort. body."""
        return cls(EExists(var, sort, body))

    @classmethod
    def forall(cls, var: str, sort: Sort, body: Expr) -> Prop:
        """∀var:sort. body."""
        return cls(EForall(var, sort, body))

    @classmethod
    def pred(cls, name: str, *args: Expr) -> Prop:
        """Predicate application: name(args...)."""
        return cls(EPred(name, args))

    @classmethod
    def eq(cls, left: Expr, right: Expr) -> Prop:
        """Equality proposition: left = right."""
        return cls(EEq(left, right))

    @staticmethod
    def var(name: str) -> Expr:
        return EVar(name)

    @staticmethod
    def const(name: str, sort: Sort) -> Expr:
        return EConst(name, sort)

    @staticmethod
    def fn(name: str, *args: Expr) -> Expr:
        return EApp(name, args)

    @staticmethod
    def nat(value: int) -> Expr:
        return ENat(value)

    @staticmethod
    def succ(term: Expr) -> Expr:
        return EApp("succ", (term,))

    @staticmethod
    def add(left: Expr, right: Expr) -> Expr:
        return EApp("add", (left, right))

    @staticmethod
    def mul(left: Expr, right: Expr) -> Expr:
        return EApp("mul", (left, right))

    @staticmethod
    def nat_sort() -> Sort:
        return "Nat"

    @staticmethod
    def sort(name: str) -> Sort:
        return name

    # ------------------------------------------------------------------
    # Coercion
    # ------------------------------------------------------------------

    @staticmethod
    def to_expr(prop_or_expr: Prop | Expr) -> Expr:
        return prop_or_expr.expr if isinstance(prop_or_expr, Prop) else prop_or_expr

    @staticmethod
    def to_prop(prop_or_expr: Prop | Expr) -> Prop:
        return prop_or_expr if isinstance(prop_or_expr, Prop) else Prop(prop_or_expr)

    # ------------------------------------------------------------------
    # Operator overloads
    # ------------------------------------------------------------------

    def __rshift__(self, other: Prop | Expr) -> Prop:
        """P >> Q  →  P → Q  (implication)."""
        return Prop(EImp(self.to_expr(self), self.to_expr(other)))

    def __and__(self, other: Prop | Expr) -> Prop:
        """P & Q  →  P ∧ Q  (conjunction)."""
        return Prop(EAnd(self.to_expr(self), self.to_expr(other)))

    def __or__(self, other: Prop | Expr) -> Prop:
        """P | Q  →  P ∨ Q  (disjunction)."""
        return Prop(EOr(self.to_expr(self), self.to_expr(other)))

    def __invert__(self) -> Prop:
        """~P  →  P → ⊥  (negation)."""
        return Prop(EImp(self.to_expr(self), EBot()))

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
