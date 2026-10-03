"""Environment storage and predefined logical declarations."""
from __future__ import annotations

from ..ast import Expr
from .declaration import Declaration
from .library import (
    BoolDeclaration,
    EmptyDeclaration,
    EqualityDeclaration,
    FinDeclaration,
    ListDeclaration,
    LogicDeclaration,
    NatDeclaration,
    OptionDeclaration,
    ProdDeclaration,
    QuotLibraryDeclaration,
    SigmaDeclaration,
    SumDeclaration,
    UnitDeclaration,
    VectorDeclaration,
)


class Environment:
    """Collection of named declarations."""

    def __init__(self):
        """Initialize an empty environment."""
        self.declarations: dict[str, Declaration] = {}

    def add(self, declaration: Declaration):
        """Add a declaration to the environment."""
        if declaration.name in self.declarations:
            raise ValueError(
                f"Declaration with name '{declaration.name}' already exists."
            )
        self.declarations[declaration.name] = declaration

    def get(self, name: str) -> Declaration | None:
        """Return the declaration with the given name, if it exists."""
        return self.declarations.get(name)

    def update(self, other: Environment):
        """Merge declarations from another environment into this one."""
        self.declarations.update(other.declarations)

    def items(self):
        """Return the environment declarations as `(name, declaration)` pairs."""
        return self.declarations.items()

    def to_context(self) -> dict[str, Expr]:
        """Convert the environment to a context dictionary mapping names to types."""
        return {name: decl.type for name, decl in self.declarations.items()}

    @classmethod
    def standard(cls) -> Environment:
        """Create a standard environment."""
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

        for item in ProdDeclaration:
            env.add(item.declaration)

        for item in SigmaDeclaration:
            env.add(item.declaration)

        for item in OptionDeclaration:
            env.add(item.declaration)

        for item in ListDeclaration:
            env.add(item.declaration)

        for item in UnitDeclaration:
            env.add(item.declaration)

        for item in SumDeclaration:
            env.add(item.declaration)

        for item in EmptyDeclaration:
            env.add(item.declaration)

        for item in FinDeclaration:
            env.add(item.declaration)

        for item in VectorDeclaration:
            env.add(item.declaration)

        for item in QuotLibraryDeclaration:
            env.add(item.declaration)

        return env
