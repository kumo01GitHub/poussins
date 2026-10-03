"""Empty: public-facing empty-type DSL."""
from __future__ import annotations

from typing import ClassVar

from ..environment.library import EmptyDeclaration
from .declared_type import DeclaredType


class Empty(DeclaredType):
    """Immutable wrapper for empty-type expressions."""

    TYPE_NAME: ClassVar[str] = EmptyDeclaration.EMPTY_DECLARATION.declaration.name
