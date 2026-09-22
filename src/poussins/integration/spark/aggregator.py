"""Aggregates executed proof declarations and updates the Environment."""
from __future__ import annotations

from ...environment import Environment, TheoremDeclaration
from ...errors import SparkIntegrationError


class ProofAggregator:
    """Aggregates executed proof declarations and updates the Environment."""

    def __init__(self, env: Environment) -> None:
        """Initialize the aggregator with a base Driver Environment."""
        self.env = env

    def assemble(
        self,
        declarations: list[TheoremDeclaration],
        main_theorem_name: str,
    ) -> Environment:
        """Assemble executed declarations and update the Environment."""
        for decl in declarations:
            if self.env.get(decl.name) is None:
                self.env.add(decl)

        if self.env.get(main_theorem_name) is None:
            raise SparkIntegrationError(
                f"Main theorem '{main_theorem_name}' was not found"
                + " in the environment after aggregation."
            )

        return self.env
