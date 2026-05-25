"""
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from poussins.ast.formulas import Formula
from poussins.kernel.goal import ProofAssurance


@dataclass(frozen=True)
class Declaration:
    name: str
    statement: Formula
    assigment: Optional[Formula]
    assurance: ProofAssurance
