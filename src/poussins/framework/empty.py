"""Empty: public-facing empty-type DSL."""
from __future__ import annotations

from typing import ClassVar

from ..environment.library import EmptyDeclaration
from .inductive_type import InductiveType


class Empty(InductiveType):
    """Immutable wrapper for empty-type expressions."""

    TYPE_NAME: ClassVar[str] = EmptyDeclaration.EMPTY_DECLARATION.declaration.name
