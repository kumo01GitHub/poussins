"""
Declaration of a named statement in the environment, which can be an axiom, theorem, lemma, etc.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..ast import Formula, ProofTerm
from ..kernel import ProofAssurance


@dataclass(frozen=True)
class Declaration:
    name: str
    statement: Formula
    assignment: Optional[ProofTerm]
    assurance: ProofAssurance
