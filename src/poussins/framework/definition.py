"""Definition in the framework."""
from __future__ import annotations

from dataclasses import dataclass

from ..ast import Expr
from ..environment import DefinitionDeclaration, Environment
from .declaration import declare_definition


@dataclass(frozen=True, init=False)
class Definition:
    """Represent a definition in the framework."""

    env: Environment
    name: str
    type: Expr
    value: Expr
    level_params: tuple[str, ...]

    def __init__(
        self,
        env: Environment,
        name: str,
        type: Expr,
        value: Expr,
        level_params: tuple[str, ...] = (),
    ) -> None:
        """Create a definition."""
        object.__setattr__(self, "env", env)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "type", type)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "level_params", level_params)

    @staticmethod
    def to_expr(value: Definition | Expr) -> Expr:
        """Return the underlying expression."""
        return value.value if isinstance(value, Definition) else value

    def declare(self) -> DefinitionDeclaration:
        """Declare the definition in the environment."""
        return declare_definition(
            env=self.env,
            name=self.name,
            type=self.type,
            value=self.value,
            level_params=self.level_params,
        )
