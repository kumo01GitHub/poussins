"""Environment storage and predefined logical declarations."""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from ..ast import Expr
from ..utils.logging import get_logger
from .declaration import ConstructorDeclaration, Declaration, InductiveDeclaration, RecursorDeclaration


class Environment:
    """Collection of named declarations."""

    def __init__(self):
        """Initialize an empty environment."""
        self.declarations: dict[str, Declaration] = {}
        self.stages: dict[str, dict[str, Declaration]] = {}
        self.logger = get_logger(__name__)

    def add(self, declaration: Declaration):
        """Add a declaration to the environment."""
        self.logger.debug(f"Adding declaration: {declaration}")
        if declaration.name in self.declarations:
            raise ValueError(
                f"Declaration with name '{declaration.name}' already exists."
            )
        self.declarations[declaration.name] = declaration
        self.logger.debug(f"Added declaration: {declaration}")

    def get(self, name: str) -> Declaration | None:
        """Return the declaration with the given name, if it exists."""
        self.logger.debug(f"Retrieving declaration for name: {name}")
        decl = self.declarations.get(name)
        self.logger.debug(
            f"Retrieved declaration: {decl}" if decl is not None
            else f"No declaration found for name: {name}"
        )
        return decl

    def get_ctors(self, for_: str | InductiveDeclaration) -> tuple[ConstructorDeclaration]:
        """Return all constructor declarations for a given inductive type."""
        self.logger.debug(f"Retrieving constructors for: {for_}")
        inductive = self.get(for_) if isinstance(for_, str) else for_
        if isinstance(inductive, InductiveDeclaration):
            self.logger.debug(f"Found inductive declaration: {inductive}")
            ctors = []
            for ctor_name in inductive.constructor_names:
                self.logger.debug(f"Retrieving constructor: {ctor_name}")
                ctor_decl = self.get(ctor_name)
                if isinstance(ctor_decl, ConstructorDeclaration):
                    self.logger.debug(f"Found constructor declaration: {ctor_decl}")
                    ctors.append(ctor_decl)
                else:
                    raise ValueError(
                        f"Constructor '{ctor_name}' for inductive '{for_}' is not a valid ConstructorDeclaration."
                    )
            self.logger.debug(f"Retrieved constructors: {ctors}")
            return tuple(ctors)
        else:
            raise ValueError(f"'{for_}' is not a valid InductiveDeclaration.")

    def get_recs(self, for_: str | InductiveDeclaration) -> tuple[RecursorDeclaration]:
        """Return all recursor declarations for a given inductive type."""
        self.logger.debug(f"Retrieving recursors for: {for_}")
        inductive = self.get(for_) if isinstance(for_, str) else for_
        if isinstance(inductive, InductiveDeclaration):
            self.logger.debug(f"Found inductive declaration: {inductive}")
            recs = []
            for rec_name in inductive.recursor_names:
                self.logger.debug(f"Retrieving recursor: {rec_name}")
                rec_decl = self.get(rec_name)
                if isinstance(rec_decl, RecursorDeclaration):
                    recs.append(rec_decl)
                else:
                    raise ValueError(
                        f"Recursor '{rec_name}' for inductive '{for_}' is not a valid RecursorDeclaration."
                    )
            self.logger.debug(f"Retrieved recursors: {recs}")
            return tuple(recs)
        else:
            raise ValueError(f"'{for_}' is not a valid InductiveDeclaration.")

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
        declarations: Sequence[Declaration],
        id_: str | None = None,
    ) -> str:
        """Stage a list of declarations under a given or auto-generated stage ID.

        Args:
            id_: Optional stage identifier. If None, a UUID is automatically generated.
            declarations: Sequence of declarations to put into this stage.

        Returns:
            The stage identifier (str).

        """
        stage_id = id_ if id_ is not None else str(uuid.uuid4())

        if stage_id not in self.stages:
            self.logger.debug(f"Creating new stage with ID: {stage_id}")
            self.stages[stage_id] = {}
        else:
            self.logger.debug(f"Using existing stage with ID: {stage_id}")

        for decl in declarations:
            if decl.name in self.declarations or decl.name in self.stages[stage_id]:
                raise ValueError(
                    f"Declaration with name '{decl.name}' already exists"
                    + " in environment or stage."
                )
            self.stages[stage_id][decl.name] = decl

        self.logger.debug(f"Staged declarations under ID '{stage_id}': {self.stages[stage_id]}")
        return stage_id

    def commit(self, id_: str):
        """Commit a staging area's declarations into the main environment.

        Args:
            id_: The stage identifier.

        """
        if id_ not in self.stages:
            raise KeyError(f"Stage ID '{id_}' does not exist.")

        staged_decls = self.stages.pop(id_)
        for name, decl in staged_decls.items():
            self.logger.debug(f"Committing declaration '{name}' from stage '{id_}' to main environment.: {decl}")
            if name in self.declarations:
                raise ValueError(
                    f"Declaration with name '{name}' already exists"
                    + " in environment during commit."
                )
            self.logger.debug(f"Committing declaration '{name}' from stage '{id_}' to main environment.")
            self.declarations[name] = decl

    def rollback(self, id_: str):
        """Discard a staging area without affecting the main environment."""
        self.logger.debug(f"Rolling back stage with ID {id_}: {self.stages.get(id_)}")
        self.stages.pop(id_, None)

    def get_staging(self, id_: str) -> Environment:
        """Return a new Environment containing main and staging declarations."""
        if id_ not in self.stages:
            raise KeyError(f"Stage ID '{id_}' does not exist.")
        new_env = Environment()
        new_env.declarations = self.declarations.copy()
        new_env.declarations.update(self.stages[id_])
        return new_env
