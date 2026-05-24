"""Formula AST nodes for propositional logic.

Defined in this module:
- FVar, FImpl, FAnd, FOr, FTrue, FFalse, FExists

Not defined here (by design):
- FNot is syntax sugar and is expanded during formula parsing
  from formula text to Formula AST:
  ~A = FImpl(A, FFalse)
- FIff is syntax sugar and is expanded during formula parsing
  from formula text to Formula AST:
  A <-> B = FAnd(FImpl(A, B), FImpl(B, A))

TODO:
- Add FAll/FExists over a proper term language (arithmetic milestone).
  The current FExists is second-order (quantifies over propositional variables).
- Add FEq with a dedicated Term AST (arithmetic milestone).
"""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass


class Formula(ABC):
    pass


@dataclass(frozen=True)
class FVar(Formula):
    """Propositional variable, e.g. P, Q."""

    name: str


@dataclass(frozen=True)
class FImpl(Formula):
    """Implication: antecedent -> consequent."""

    antecedent: Formula
    consequent: Formula


@dataclass(frozen=True)
class FAnd(Formula):
    """Conjunction: left /\\ right."""

    left: Formula
    right: Formula


@dataclass(frozen=True)
class FOr(Formula):
    """Disjunction: left \\/ right."""

    left: Formula
    right: Formula


@dataclass(frozen=True)
class FTrue(Formula):
    """Logical true (top)."""


@dataclass(frozen=True)
class FFalse(Formula):
    """Logical false (bottom)."""


@dataclass(frozen=True)
class FExists(Formula):
    """Existential quantification over a propositional variable: ∃var. body.

    ``var`` is the name of a bound propositional variable (an FVar name).
    ``body`` is the formula with ``var`` potentially free.
    """

    var: str
    body: Formula
