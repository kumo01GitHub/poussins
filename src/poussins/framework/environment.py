"""
Environment: a collection of declarations (axioms, theorems, etc.) with unique names.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Final, Optional

from ..ast import Formula, FTrue, ProofTerm, PTrueI
from ..errors import FrameworkError
from ..kernel import ProofAssurance


@dataclass(frozen=True)
class Declaration:
    name: str
    statement: Formula
    assignment: Optional[ProofTerm]
    assurance: ProofAssurance


DECLARATION_TOP: Final[Declaration] = Declaration(
    name="TOP",
    statement=FTrue(),
    assignment=PTrueI(),
    assurance=ProofAssurance.VERIFIED,
)


@dataclass
class Environment:
    declarations: dict[str, Declaration] = field(default_factory=dict)

    def add(self, declaration: Declaration, name: Optional[str]=None):
        if declaration.name == DECLARATION_TOP.name:
            raise FrameworkError("Cannot add a declaration with the reserved name 'TOP'.")
        key = name if name is not None else declaration.name
        self.declarations[key] = declaration

    def get(self, name: str) -> Optional[Declaration]:
        if name == DECLARATION_TOP.name:
            return DECLARATION_TOP
        return self.declarations.get(name)

    def update(self, other: Environment):
        self.declarations.update(other.declarations)

    def items(self):
        return self.declarations.items()
