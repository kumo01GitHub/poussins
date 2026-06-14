"""
Prop: public-facing propositional formula DSL.

Wraps the internal Formula AST with Python operator overloads so that
propositions can be written naturally in Python code:

    p, q = Prop("P"), Prop("Q")
    p >> q        # P → Q  (implication)
    p & q         # P ∧ Q  (conjunction)
    p | q         # P ∨ Q  (disjunction)
    ~p            # ¬P     (negation, sugar for P → ⊥)
    Prop.top()    # ⊤
    Prop.bot()    # ⊥
    Prop.exists("x", p)  # ∃x. P

Prop is immutable.  The underlying Formula is accessible via .formula.
"""

from __future__ import annotations
from dataclasses import dataclass

from poussins.ast import (
    Formula,
    FVar,
    FTrue,
    FFalse,
    FExists,
    FAnd,
    FImpl,
    FOr
)


@dataclass(frozen=True)
class Prop:
    def __init__(self, formula: Formula | str) -> None:
        if isinstance(formula, Formula):
            object.__setattr__(self, "formula", formula)
        else:
            object.__setattr__(self, "formula", FVar(formula))

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def top(cls) -> Prop:
        """⊤ (True)."""
        return cls(FTrue())

    @classmethod
    def bot(cls) -> Prop:
        """⊥ (False)."""
        return cls(FFalse())

    @classmethod
    def exists(cls, var: str, body: Formula) -> Prop:
        """∃var. body."""
        return cls(FExists(var, body))

    # ------------------------------------------------------------------
    # Coercion
    # ------------------------------------------------------------------

    @staticmethod
    def to_formula(prop_or_formula: Prop | Formula) -> Formula:
        return prop_or_formula.formula if isinstance(prop_or_formula, Prop) else prop_or_formula

    @staticmethod
    def to_prop(prop_or_formula: Prop | Formula) -> Prop:
        return prop_or_formula if isinstance(prop_or_formula, Prop) else Prop(prop_or_formula)

    # ------------------------------------------------------------------
    # Operator overloads
    # ------------------------------------------------------------------

    def __rshift__(self, other: Prop | Formula) -> Prop:
        """P >> Q  →  P → Q  (implication)."""
        return Prop(FImpl(self.to_formula(self), self.to_formula(other)))

    def __and__(self, other: Prop | Formula) -> Prop:
        """P & Q  →  P ∧ Q  (conjunction)."""
        return Prop(FAnd(self.to_formula(self), self.to_formula(other)))

    def __or__(self, other: Prop | Formula) -> Prop:
        """P | Q  →  P ∨ Q  (disjunction)."""
        return Prop(FOr(self.to_formula(self), self.to_formula(other)))

    def __invert__(self) -> Prop:
        """~P  →  P → ⊥  (negation)."""
        return Prop(FImpl(self.to_formula(self), FFalse()))

    # ------------------------------------------------------------------
    # Equality / hashing — delegate to Formula
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Prop):
            return self.formula == other.formula
        elif isinstance(other, Formula):
            return self.formula == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.formula)

    def __repr__(self) -> str:
        return f"Prop({self.formula!r})"
