"""Inductive type expressions."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import ClassVar, override

from ..ast import (
    EFVar,
    Expr,
    app,
)
from ..environment import Environment, InductiveDeclaration, InductiveSpec, const
from ..environment.library import EQ_IND_SPEC
from .bound_var import BindableMixin
from .declaration import declare_inductive
from .environment import STANDARD_ENV


@dataclass(frozen=True)
class Inductive(BindableMixin, ABC):
    """Immutable wrapper for inductive type expressions."""

    SPEC: ClassVar[InductiveSpec | None] = None
    _env: ClassVar[Environment | None] = None

    value: Expr

    def __init__(self, value: Expr | str) -> None:
        """Initialize an inductive type."""
        if isinstance(value, Expr):
            object.__setattr__(self, "value", value)
        else:
            object.__setattr__(self, "value", EFVar(value))

    @classmethod
    def declare(cls, env: Environment) -> InductiveDeclaration:
        """Declare the inductive type in the environment."""
        if cls.SPEC is None:
            raise NotImplementedError
        declaration = declare_inductive(env, cls.SPEC)
        cls._env = env
        return declaration

    @classmethod
    def env(cls) -> Environment | None:
        """Return the environment in which this inductive type is declared."""
        return getattr(cls, "_env", None)

    @staticmethod
    def to_expr(value: Inductive | Expr) -> Expr:
        """Return the underlying expression."""
        return value.value if isinstance(value, Inductive) else value

    @classmethod
    def spec(cls) -> InductiveSpec:
        """Return the inductive specification for this class."""
        if cls.SPEC is None:
            raise NotImplementedError
        return cls.SPEC

    @classmethod
    def constructor_name(cls, index: int) -> str:
        """Return constructor name by index from this inductive spec."""
        return cls.spec().constructors[index][0]

    @classmethod
    def type_ref(cls) -> Expr:
        """Return the type expression of this inductive type."""
        env = cls.env()
        return const(env if env is not None else STANDARD_ENV, cls.spec().name)

    @property
    def type(self) -> Expr:
        """Return the type expression of this inductive type instance."""
        return self.type_ref()

    @classmethod
    def eq(
        cls,
        left: Inductive | Expr,
        right: Inductive | Expr,
    ) -> Expr:
        """Return the equality proposition between two inductive values."""
        env = cls.env()
        return app(
            const(
                env if env is not None else STANDARD_ENV,
                EQ_IND_SPEC.name
            ),
            cls.type_ref(),
            cls.to_expr(left),
            cls.to_expr(right),
        )

    @property
    @override
    def bound_type(self) -> Expr:
        """Return the type of the bound variable."""
        return self.type

    @property
    @override
    def bound_value(self) -> Expr:
        """Return the value of the bound variable."""
        return self.value


def inductive_type[T: Inductive](spec: InductiveSpec):
    """Define an inductive type class with the given specification."""

    def decorator(cls: type[T]) -> type[T]:
        cls.SPEC = spec
        cls._env = None

        return cls

    return decorator
