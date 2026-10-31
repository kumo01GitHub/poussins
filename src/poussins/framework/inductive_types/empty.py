"""Empty: public-facing empty-type DSL."""
from __future__ import annotations

from dataclasses import dataclass

from ...environment.library import EMPTY_IND_SPEC
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=EMPTY_IND_SPEC)
class Empty(Inductive):
    """Immutable wrapper for empty-type expressions."""
