"""Empty declarations."""
from __future__ import annotations

from enum import Enum

from ..declaration import Declaration, InductiveDeclaration
from .sort import Sort


class EmptyDeclaration(Enum):
    """Inductive declaration for Empty."""

    EMPTY_DECLARATION = InductiveDeclaration(
        name="Empty",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=(),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
