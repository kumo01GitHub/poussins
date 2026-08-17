"""
Environment storage and predefined logical declarations.
"""
from __future__ import annotations

from .declaration import Declaration
from .library import (
    LogicDeclaration,
    EqualityDeclaration,
    BoolDeclaration,
    NatDeclaration,
)
from ..ast import Expr


class Environment:
    """
    Collection of named declarations used by the proof engine.
    """

    def __init__(self):
        self.declarations: dict[str, Declaration] = {}

    def add(self, declaration: Declaration):
        """
        Add a declaration to the environment.
        """
        if declaration.name in self.declarations:
            raise ValueError(f"Declaration with name '{declaration.name}' already exists.")
        self.declarations[declaration.name] = declaration

    def get(self, name: str) -> Declaration | None:
        """
        Return the declaration with the given name, if it exists.
        """
        return self.declarations.get(name)

    def update(self, other: "Environment"):
        """
        Merge declarations from another environment into this one.
        """
        self.declarations.update(other.declarations)

    def items(self):
        """
        Return the environment declarations as `(name, declaration)` pairs.
        """
        return self.declarations.items()

    def to_context(self) -> dict[str, Expr]:
        """
        Convert the environment to a context dictionary mapping names to types.
        """
        return {name: decl.type for name, decl in self.declarations.items()}

    @classmethod
    def standard(cls) -> "Environment":
        """
        Create a standard environment with the core logical declarations.
        """
        env = cls()

        # ------------------------------------------------------------------
        # Logical Declarations
        # ------------------------------------------------------------------
        for item in LogicDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Equality Declarations
        # ------------------------------------------------------------------
        for item in EqualityDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Boolean Declarations
        # ------------------------------------------------------------------
        for item in BoolDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Natural Number Declarations
        # ------------------------------------------------------------------
        for item in NatDeclaration:
            env.add(item.declaration)

        return env
