"""Bool: public-facing boolean DSL.

This wraps the internal Expr AST for boolean values so data-level booleans can
be manipulated ergonomically from Python.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...environment import const
from ...environment.library import BOOL_IND_SPEC
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=BOOL_IND_SPEC)
class Bool(Inductive):
    """Immutable wrapper for boolean expressions."""

    TRUE_IDX: ClassVar[int] = 0
    FALSE_IDX: ClassVar[int] = 1

    @classmethod
    def true(cls) -> Bool:
        """Construct the true boolean value."""
        env = cls.env()
        return cls(
            const(
                env=env if env is not None else STANDARD_ENV,
                name=cls.CONSTRUCTORS[cls.TRUE_IDX][0],
            )
        )

    @classmethod
    def false(cls) -> Bool:
        """Construct the false boolean value."""
        env = cls.env()
        return cls(
            const(
                env=env if env is not None else STANDARD_ENV,
                name=cls.CONSTRUCTORS[cls.FALSE_IDX][0],
            )
        )
