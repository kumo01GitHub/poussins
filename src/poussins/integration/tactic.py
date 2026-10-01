"""Tactic plan schemas and serialization helpers."""
from __future__ import annotations

import json

from ..ast import Expr, ExprSerializer

type TacticArg = str | int | list[str] | frozenset[str] | tuple | Expr | None
type TacticPlan = tuple[str, dict[str, TacticArg]]


class TacticPlanSerializer:
    """Serializes and deserializes TacticPlan instances."""

    @staticmethod
    def _normalize(value):
        """Normalize a value for JSON serialization."""
        if isinstance(value, list):
            return [TacticPlanSerializer._normalize(item) for item in value]
        if isinstance(value, frozenset):
            return [TacticPlanSerializer._normalize(item) for item in sorted(value)]
        if isinstance(value, tuple):
            return [TacticPlanSerializer._normalize(item) for item in value]
        if isinstance(value, Expr):
            return ExprSerializer.to_dict(value)
        return value

    @classmethod
    def to_dict(cls, plan: TacticPlan) -> dict:
        """Convert a TacticPlan instance into a JSON-safe dictionary."""
        tactic, args = plan
        return {
            "tactic": tactic,
            "args": {
                # TODO: Consider Expr | str case.
                key: cls._normalize(value) for key, value in args.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> TacticPlan:
        """Convert a dictionary into a TacticPlan instance."""
        if "tactic" not in data:
            raise ValueError("Missing 'tactic' key in TacticPlan data.")
        if "args" not in data:
            raise ValueError("Missing 'args' key in TacticPlan data.")

        tactic = data["tactic"]
        raw_args = data["args"]
        if not isinstance(raw_args, dict):
            raise ValueError("Tactic args must be a dictionary.")

        return (tactic, raw_args)

    @classmethod
    def serialize(cls, plan: TacticPlan) -> str:
        """Serialize a TacticPlan instance into a JSON string."""
        return json.dumps(cls.to_dict(plan))

    @classmethod
    def deserialize(cls, json_str) -> TacticPlan:
        """Deserialize a JSON string into a TacticPlan instance."""
        return cls.from_dict(json.loads(json_str))
