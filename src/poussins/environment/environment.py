"""Environment storage and predefined logical declarations."""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from ..ast import Expr
from .declaration import Declaration


class Environment:
    """Collection of named declarations."""

    def __init__(self):
        """Initialize an empty environment."""
        self.declarations: dict[str, Declaration] = {}
        self.stages: dict[str, dict[str, Declaration]] = {}

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

    def has(self, name: str) -> bool:
        """Check if a declaration with the given name exists in the environment."""
        return name in self.declarations

    def update(self, other: Environment):
        """Merge declarations from another environment into this one."""
        self.declarations.update(other.declarations)

    def items(self):
        """Return the environment declarations as `(name, declaration)` pairs."""
        return self.declarations.items()

    def to_context(self) -> dict[str, Expr]:
        """Convert the environment to a context dictionary mapping names to types."""
        return {name: decl.type for name, decl in self.declarations.items()}

    def stage(
        self,
        id: str | None = None,
        declarations: Sequence[Declaration] | None = None,
    ) -> str:
        """Stage a list of declarations under a given or auto-generated stage ID.

        Args:
            id: Optional stage identifier. If None, a UUID is automatically generated.
            declarations: Sequence of declarations to put into this stage.

        Returns:
            The stage identifier (str).

        """
        stage_id = id if id is not None else str(uuid.uuid4())

        if stage_id not in self.stages:
            self.stages[stage_id] = {}

        if declarations is not None:
            for decl in declarations:
                if decl.name in self.declarations or decl.name in self.stages[stage_id]:
                    raise ValueError(
                        f"Declaration with name '{decl.name}' already exists in environment or stage."
                    )
                self.stages[stage_id][decl.name] = decl

        return stage_id

    def commit(self, id: str):
        """Commit a staging area's declarations into the main environment and clean up."""
        if id not in self.stages:
            raise KeyError(f"Stage ID '{id}' does not exist.")

        staged_decls = self.stages.pop(id)
        for name, decl in staged_decls.items():
            if name in self.declarations:
                raise ValueError(
                    f"Declaration with name '{name}' already exists in environment during commit."
                )
            self.declarations[name] = decl

    def rollback(self, id: str):
        """Discard a staging area without affecting the main environment."""
        self.stages.pop(id, None)

    def get_staging(self, id: str) -> Environment:
        """Return a new Environment instance containing only the declarations in the specified stage."""
        if id not in self.stages:
            raise KeyError(f"Stage ID '{id}' does not exist.")

        new_env = Environment()
        new_env.declarations = self.stages[id].copy()
        return new_env
