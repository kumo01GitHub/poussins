"""Tactic plan schemas and serialization helpers."""
from __future__ import annotations

import json
from typing import cast

from ..ast import Expr, ExprSerializer

type TacticArg = str | int | list[str] | frozenset[str] | tuple | Expr | None
type TacticPlan = tuple[str, dict[str, TacticArg]]
type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


class TacticPlanSerializer:
    """Serializes and deserializes TacticPlan instances."""

    @staticmethod
    def _encode(value: TacticArg) -> JsonValue:
        """Encode tactic argument values into JSON-safe tagged structures."""
        if isinstance(value, list):
            return [
                TacticPlanSerializer._encode(cast(TacticArg, item))
                for item in value
            ]
        if isinstance(value, frozenset):
            return {
                "__kind": "frozenset",
                "items": [
                    TacticPlanSerializer._encode(cast(TacticArg, item))
                    for item in sorted(value)
                ],
            }
        if isinstance(value, tuple):
            return {
                "__kind": "tuple",
                "items": [
                    TacticPlanSerializer._encode(cast(TacticArg, item))
                    for item in value
                ],
            }
        if isinstance(value, Expr):
            return {
                "__kind": "expr",
                "value": ExprSerializer.to_dict(value),
            }
        return value

    @staticmethod
    def _decode(value: JsonValue) -> TacticArg:
        """Decode tagged JSON values back into tactic argument runtime values."""
        if isinstance(value, list):
            decoded = [TacticPlanSerializer._decode(item) for item in value]
            if any(not isinstance(item, str) for item in decoded):
                raise ValueError("List tactic argument must contain only strings.")
            return cast(list[str], decoded)
        if isinstance(value, dict):
            kind = value.get("__kind")
            if not isinstance(kind, str):
                raise ValueError("Dictionary tactic argument must include '__kind'.")
            if kind == "expr":
                raw_expr = value.get("value")
                if not isinstance(raw_expr, dict):
                    raise ValueError("Invalid expr payload in tactic argument.")
                return cast(
                    TacticArg,
                    ExprSerializer.from_dict(cast(dict[str, object], raw_expr)),
                )
            if kind == "tuple":
                raw_items = value.get("items")
                if not isinstance(raw_items, list):
                    raise ValueError("Invalid tuple payload in tactic argument.")
                return cast(
                    TacticArg,
                    tuple(TacticPlanSerializer._decode(item) for item in raw_items),
                )
            if kind == "frozenset":
                raw_items = value.get("items")
                if not isinstance(raw_items, list):
                    raise ValueError("Invalid frozenset payload in tactic argument.")
                decoded_items = [
                    TacticPlanSerializer._decode(item) for item in raw_items
                ]
                if any(not isinstance(item, str) for item in decoded_items):
                    raise ValueError(
                        "frozenset tactic argument must contain only strings."
                    )
                return cast(
                    TacticArg,
                    frozenset(cast(str, item) for item in decoded_items),
                )
            raise ValueError(f"Unknown tactic argument kind: {kind}")

        if value is None or isinstance(value, str):
            return value
        if type(value) is int:
            return value
        raise ValueError(f"Unsupported tactic argument value: {value!r}")

    @classmethod
    def to_dict(cls, plan: TacticPlan) -> dict[str, JsonValue]:
        """Convert a TacticPlan instance into a JSON-safe dictionary."""
        tactic, args = plan
        return {
            "tactic": tactic,
            "args": {
                key: cls._encode(value) for key, value in args.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TacticPlan:
        """Convert a dictionary into a TacticPlan instance."""
        if "tactic" not in data:
            raise ValueError("Missing 'tactic' key in TacticPlan data.")
        if "args" not in data:
            raise ValueError("Missing 'args' key in TacticPlan data.")

        tactic = data["tactic"]
        if not isinstance(tactic, str):
            raise ValueError("Tactic name must be a string.")
        raw_args = data["args"]
        if not isinstance(raw_args, dict):
            raise ValueError("Tactic args must be a dictionary.")

        args = {
            key: cast(TacticArg, cls._decode(cast(JsonValue, value)))
            for key, value in raw_args.items()
        }

        return (tactic, args)

    @classmethod
    def serialize(cls, plan: TacticPlan) -> str:
        """Serialize a TacticPlan instance into a JSON string."""
        return json.dumps(cls.to_dict(plan))

    @classmethod
    def deserialize(cls, json_str: str) -> TacticPlan:
        """Deserialize a JSON string into a TacticPlan instance."""
        return cls.from_dict(json.loads(json_str))
