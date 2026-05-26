"""
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import uuid4

from ..ast.proof_terms import ProofTerm, Formula


class ProofAssurance(str, Enum):
    """Verification assurance axis."""

    UNKNOWN = "unknown"
    VERIFIED = "verified"
    TRUSTED = "trusted"
    ADMITTED = "admitted"
    INVALID = "invalid"


@dataclass(frozen=True)
class Context:
    hyps: Dict[str, Formula]

    def get(self, name: str) -> Optional[Formula]:
        return self.hyps.get(name)

    def add(self, additional_hyps: Dict[str, Formula]) -> Context:
        new_hyps = dict(self.hyps)
        new_hyps.update(additional_hyps)
        return Context(hyps=new_hyps)


@dataclass
class Goal:
    id: str = field(init=False)
    formula: Formula
    context: Context
    assignment: Optional[ProofTerm] = None
    assurance: ProofAssurance = ProofAssurance.UNKNOWN

    def __post_init__(self):
        self.id = str(uuid4())

    @property
    def is_closed(self) -> bool:
        if self.assignment is None:
            return False
        else:
            return not self.assignment.has_meta_var

    def __eq__(self, other: Goal) -> bool:
        return self.id == other.id
