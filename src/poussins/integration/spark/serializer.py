"""Serialization and deserialization utilities for ProofTaskNode instances."""
from __future__ import annotations

from typing import cast

from ...ast import ExprSerializer, SerializedExpr
from .task import ProofTaskNode, TacticRecipeItem

type SerializedTaskNode = dict[
    str, str | SerializedExpr | list[TacticRecipeItem] | list[str]
]


class ProofTaskSerializer:
    """Serializes and deserializes ProofTaskNode instances."""

    @classmethod
    def serialize(cls, node: ProofTaskNode) -> SerializedTaskNode:
        """Serialize a ProofTaskNode instance into a dictionary."""
        return {
            "name": node.name,
            "statement": ExprSerializer.serialize(node.statement),
            "tactic_recipe": node.tactic_recipe,
            "depends_on": node.depends_on,
        }

    @classmethod
    def deserialize(cls, data: SerializedTaskNode) -> ProofTaskNode:
        """Deserialize a dictionary into a ProofTaskNode instance."""
        return ProofTaskNode(
            name=cast(str, data["name"]),
            statement=ExprSerializer.deserialize(
                cast(SerializedExpr, data["statement"])
            ),
            tactic_recipe=cast(list[TacticRecipeItem], data["tactic_recipe"]),
            depends_on=cast(list[str], data.get("depends_on", [])),
        )
