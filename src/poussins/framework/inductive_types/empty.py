"""Empty: public-facing empty-type DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...environment.library import EmptyDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Empty(Inductive):
    """Immutable wrapper for empty-type expressions."""

    TYPE_NAME: ClassVar[str] = EmptyDeclaration.EMPTY_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        EmptyDeclaration.EMPTY_DECLARATION.declaration.level_params
    )
