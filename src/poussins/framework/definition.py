"""Definition in the framework."""
from __future__ import annotations

from dataclasses import dataclass

from ..ast import Expr
from ..environment import DefinitionDeclaration, DefinitionSpec, Environment
from .declaration import declare_definition


@dataclass(frozen=True, init=False)
class Definition:
    """Represent a definition in the framework."""

    name: str
    type: Expr
    value: Expr

    def __init__(
        self,
        name: str,
        type_: Expr,
        value: Expr,
    ) -> None:
        """Create a definition."""
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "type", type_)
        object.__setattr__(self, "value", value)

    @staticmethod
    def to_expr(value: Definition | Expr) -> Expr:
        """Return the underlying expression."""
        return value.value if isinstance(value, Definition) else value

    def declare(self, env: Environment) -> DefinitionDeclaration:
        """Declare the definition in the environment."""
        return declare_definition(
            env=env,
            spec=DefinitionSpec(
                name=self.name,
                type=self.type,
                value=self.value,
            ),
        )
