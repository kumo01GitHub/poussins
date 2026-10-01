"""Serialization and deserialization utilities for ProofTaskNode instances."""
from __future__ import annotations

import json
from typing import cast

from ...ast import ExprSerializer
from ..tactic import TacticPlanSerializer
from .task import ProofTaskNode


class ProofTaskSerializer:
    """Serializes and deserializes ProofTaskNode instances."""

    @classmethod
    def to_dict(cls, node: ProofTaskNode) -> dict:
        """Convert a ProofTaskNode instance into a dictionary."""
        return {
            "name": node.name,
            "statement": ExprSerializer.to_dict(node.statement),
            "tactic_plan": [
                TacticPlanSerializer.to_dict(plan) for plan in node.tactic_plan
            ],
            "depends_on": node.depends_on,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProofTaskNode:
        """Convert a dictionary into a ProofTaskNode instance."""
        if "name" not in data or "statement" not in data or "tactic_plan" not in data:
            raise ValueError(
                "Missing required keys in ProofTaskNode data. "
                "Required keys: 'name', 'statement', 'tactic_plan'."
            )

        return ProofTaskNode(
            name=cast(str, data["name"]),
            statement=ExprSerializer.from_dict(cast(dict, data["statement"])),
            tactic_plan=[
                TacticPlanSerializer.from_dict(cast(dict, plan))
                for plan in cast(list[dict], data["tactic_plan"])
            ],
            depends_on=data.get("depends_on", [])
        )

    @classmethod
    def serialize(cls, node: ProofTaskNode) -> str:
        """Serialize a ProofTaskNode instance into a JSON string."""
        return json.dumps(cls.to_dict(node))

    @classmethod
    def deserialize(cls, json_str) -> ProofTaskNode:
        """Deserialize a JSON string into a ProofTaskNode instance."""
        return cls.from_dict(json.loads(json_str))
