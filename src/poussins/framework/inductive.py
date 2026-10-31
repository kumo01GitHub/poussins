"""Inductive type expressions."""
from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, override

from ..ast import (
    EVar,
    Expr,
    Sort,
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

    NAME: ClassVar[str] = "__undefined__"
    TYPE: ClassVar[Expr] = Sort.TYPE.sort
    CONSTRUCTORS: ClassVar[Sequence[tuple[str, Expr]]] = ()

    value: Expr

    def __init__(self, value: Expr | str) -> None:
        """Initialize an inductive type."""
        if isinstance(value, Expr):
            object.__setattr__(self, "value", value)
        else:
            object.__setattr__(self, "value", EVar(value))

    @classmethod
    def declare(cls, env: Environment) -> InductiveDeclaration:
        """Declare the inductive type in the environment."""
        raise NotImplementedError

    @classmethod
    def env(cls) -> Environment | None:
        """Return the environment in which this inductive type is declared."""
        return getattr(cls, "_env", None)

    @staticmethod
    def to_expr(value: Inductive | Expr) -> Expr:
        """Return the underlying expression."""
        return value.value if isinstance(value, Inductive) else value

    @classmethod
    def type_ref(cls) -> Expr:
        """Return the type expression of this inductive type."""
        env = cls.env()
        return const(env if env is not None else STANDARD_ENV, cls.NAME)

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
        cls.NAME = spec.name
        cls.TYPE = spec.type
        cls.CONSTRUCTORS = spec.constructors

        _env: Environment | None = None

        @override
        @classmethod
        def declare(cls, env: Environment) -> InductiveDeclaration:
            declaration = declare_inductive(env, spec)
            cls._env = env
            return declaration

        @override
        @classmethod
        def env(cls) -> Environment | None:
            return cls._env

        return cls

    return decorator
