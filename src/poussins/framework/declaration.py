"""
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..ast.formulas import Formula
from ..ast.proof_terms import ProofTerm
from ..kernel.goal import ProofAssurance


@dataclass(frozen=True)
class Declaration:
    name: str
    statement: Formula
    assignment: Optional[ProofTerm]
    assurance: ProofAssurance
