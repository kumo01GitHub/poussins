"""Unit: public-facing unit-value DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...environment import const
from ...environment.library import UNIT_IND_SPEC
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=UNIT_IND_SPEC)
class Unit(Inductive):
    """Immutable wrapper for unit expressions."""

    UNIT_IDX: ClassVar[int] = 0

    @classmethod
    def unit(cls) -> Unit:
        """Construct the unique unit value."""
        env = cls.env()
        return cls(
            const(
                env=env if env is not None else STANDARD_ENV,
                name=cls.CONSTRUCTORS[cls.UNIT_IDX][0],
            )
        )
