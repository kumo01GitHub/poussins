"""
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .declaration import Declaration
from ..kernel.goal import ProofAssurance


@dataclass
class Environment:
    declarations: dict[str, Declaration] = field(default_factory=dict)

    def add(self, declaration: Declaration, name: Optional[str]=None):
        if declaration.assurance == ProofAssurance.VERIFIED and declaration.assignment is None:
            raise ValueError("Verified declaration must have an assignment.")

        key = name if name is not None else declaration.name
        self.declarations[key] = declaration

    def get(self, name: str) -> Optional[Declaration]:
        return self.declarations.get(name)

    def update(self, other: Environment):
        self.declarations.update(other.declarations)
