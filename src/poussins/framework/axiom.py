"""
A named proposition accepted without proof.
"""
from __future__ import annotations
from logging import Logger
from typing import Final

from .prop import Prop
from ..ast import Expr
from ..environment import Environment, AxiomDeclaration
from ..errors import FrameworkError
from ..utils.logging import getLogger


class Axiom:
    """
    Represent a proposition accepted without proof.
    """

    def __init__(
        self,
        name: str,
        statement: Prop | Expr,
        env: Environment,
        level_params: tuple[str, ...] = (),
    ) -> None:
        """
        Create an axiom with a name, statement, environment, and universe parameters.
        """
        self.name: Final[str] = name
        self.level_params: Final[tuple[str, ...]] = level_params
        self.statement: Final[Expr] = Prop.to_expr(statement)
        self.env: Final[Environment] = env
        self.logger: Final[Logger] = getLogger(__name__)

        self.declare()

    def declare(self) -> None:
        """
        Declare the axiom in the environment.
        """
        declaration = AxiomDeclaration(
            name=self.name,
            level_params=self.level_params,
            type=self.statement,
        )

        try:
            self.env.add(declaration)
            self.logger.info(f"Axiom '{self.name}' is successfully declared: {self.statement}")
        except ValueError as e:
            raise FrameworkError(f"Failed to register axiom '{self.name}': {e}")
