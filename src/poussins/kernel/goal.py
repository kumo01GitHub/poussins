"""
Kernel-level components of the proof system, including the core data structures and proof engine.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import uuid4

from ..ast import (
    ProofTerm,
    Expr,
    Sort,
    FunctionSymbol,
)


def _default_sort_ctx() -> Dict[str, Sort]:
    return {
        "Prop": "Prop",
    }


class ProofAssurance(str, Enum):
    """Verification assurance axis."""

    UNKNOWN = "unknown"
    VERIFIED = "verified"
    TRUSTED = "trusted"
    ADMITTED = "admitted"
    INVALID = "invalid"


@dataclass(frozen=True)
class Context:
    hyp_ctx: Dict[str, Expr]
    term_ctx: Dict[str, Sort] = field(default_factory=dict)
    sort_ctx: Dict[str, Sort] = field(default_factory=_default_sort_ctx)
    fn_symbols: Dict[str, FunctionSymbol] = field(default_factory=dict)

    def get(self, name: str) -> Optional[Expr]:
        return self.hyp_ctx.get(name)

    def add(self, additional_hyps: Dict[str, Expr]) -> Context:
        new_hyps = dict(self.hyp_ctx)
        new_hyps.update(additional_hyps)
        return Context(
            hyp_ctx=new_hyps,
            term_ctx=self.term_ctx,
            sort_ctx=self.sort_ctx,
            fn_symbols=self.fn_symbols,
        )

    def delete(self, name: str) -> Context:
        new_hyps = dict(self.hyp_ctx)
        if name in new_hyps:
            del new_hyps[name]
        return Context(
            hyp_ctx=new_hyps,
            term_ctx=self.term_ctx,
            sort_ctx=self.sort_ctx,
            fn_symbols=self.fn_symbols,
        )

    def items(self):
        return self.hyp_ctx.items()

    def get_term_sort(self, name: str) -> Optional[Sort]:
        return self.term_ctx.get(name)

    def add_terms(self, additional_terms: Dict[str, Sort]) -> Context:
        new_terms = dict(self.term_ctx)
        new_terms.update(additional_terms)
        return Context(
            hyp_ctx=self.hyp_ctx,
            term_ctx=new_terms,
            sort_ctx=self.sort_ctx,
            fn_symbols=self.fn_symbols,
        )

    def add_sorts(self, sorts: Dict[str, Sort]) -> Context:
        new_sorts = dict(self.sort_ctx)
        new_sorts.update(sorts)
        return Context(
            hyp_ctx=self.hyp_ctx,
            term_ctx=self.term_ctx,
            sort_ctx=new_sorts,
            fn_symbols=self.fn_symbols,
        )

    def is_declared_sort(self, sort: Sort) -> bool:
        return any(declared_sort == sort for declared_sort in self.sort_ctx.values())

    def add_fn_symbols(self, symbols: Dict[str, FunctionSymbol]) -> Context:
        new_symbols = dict(self.fn_symbols)
        new_symbols.update(symbols)
        return Context(
            hyp_ctx=self.hyp_ctx,
            term_ctx=self.term_ctx,
            sort_ctx=self.sort_ctx,
            fn_symbols=new_symbols,
        )


@dataclass
class Goal:
    id: str = field(init=False)
    formula: Expr
    context: Context
    assignment: Optional[ProofTerm] = None
    assurance: ProofAssurance = ProofAssurance.UNKNOWN

    def __post_init__(self):
        self.id = str(uuid4())

    @property
    def is_closed(self) -> bool:
        return (
            self.assignment is not None
            and self.assurance in {
                ProofAssurance.VERIFIED,
                ProofAssurance.TRUSTED,
            }
        )

    def __eq__(self, other: Goal) -> bool:
        return self.id == other.id
