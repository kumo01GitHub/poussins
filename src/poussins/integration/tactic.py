"""Tactic plan schemas and serialization helpers."""
from __future__ import annotations

from typing import cast

from ..ast import Expr
from ..framework.proof_script import ExprLike
from .expr import ExprSerializer
from .serializer import JsonValue, Serializer

type TacticArg = str | int | list[str] | set[str] | tuple | Expr | ExprLike | None
type TacticPlan = tuple[str, dict[str, TacticArg]]


class ExprLikeSerializer(Serializer[ExprLike]):
    """Serializes and deserializes ExprLike instances."""

    @classmethod
    def to_dict(cls, obj: ExprLike) -> dict[str, JsonValue]:
        """Convert an ExprLike instance into a dictionary."""
        if isinstance(obj, Expr):
            return {
                "__kind": "expr",
                "value": ExprSerializer.to_dict(obj),
            }
        return {
            "__kind": "prop",
            "value": ExprSerializer.to_dict(obj.expr),
        }

    @classmethod
    def from_dict(cls, data: dict[str, JsonValue]) -> ExprLike:
        """Convert a dictionary into an ExprLike instance."""
        kind = data.get("__kind")
        if kind == "expr":
            raw_expr = data.get("value")
            if not isinstance(raw_expr, dict):
                msg = "Invalid expr payload in ExprLike."
                raise ValueError(msg)
            return cast(
                ExprLike,
                ExprSerializer.from_dict(cast(dict[str, JsonValue], raw_expr)),
            )
        if kind == "prop":
            raw_expr = data.get("value")
            if not isinstance(raw_expr, dict):
                msg = "Invalid prop payload in ExprLike."
                raise ValueError(msg)
            expr = cast(
                Expr,
                ExprSerializer.from_dict(cast(dict[str, JsonValue], raw_expr)),
            )
            return cast(ExprLike, expr)
        msg = f"Unknown kind in ExprLike: {kind}"
        raise ValueError(msg)


class TacticPlanSerializer(Serializer[TacticPlan]):
    """Serializes and deserializes TacticPlan instances."""

    @staticmethod
    def encode_arg(value: TacticArg) -> JsonValue:
        """Encode tactic argument values into JSON-safe tagged structures."""
        if isinstance(value, list):
            return [
                TacticPlanSerializer.encode_arg(cast(TacticArg, item))
                for item in value
            ]
        if isinstance(value, set):
            return {
                "__kind": "set",
                "items": [
                    TacticPlanSerializer.encode_arg(cast(TacticArg, item))
                    for item in sorted(value)
                ],
            }
        if isinstance(value, tuple):
            return {
                "__kind": "tuple",
                "items": [
                    TacticPlanSerializer.encode_arg(cast(TacticArg, item))
                    for item in value
                ],
            }
        if isinstance(value, Expr):
            return {
                "__kind": "expr",
                "value": ExprSerializer.to_dict(value),
            }
        if isinstance(value, Prop):
            return {
                "__kind": "prop",
                "value": ExprSerializer.to_dict(value.expr),
            }
        return value

    @staticmethod
    def decode_arg(value: JsonValue) -> TacticArg:
        """Decode tagged JSON values back into tactic argument runtime values."""
        if isinstance(value, list):
            decoded = [TacticPlanSerializer.decode_arg(item) for item in value]
            if any(not isinstance(item, str) for item in decoded):
                msg = "List tactic argument must contain only strings."
                raise ValueError(msg)
            return cast(list[str], decoded)
        if isinstance(value, dict):
            kind = value.get("__kind")
            if not isinstance(kind, str):
                msg = "Dictionary tactic argument must include '__kind'."
                raise ValueError(msg)
            if kind == "expr":
                raw_expr = value.get("value")
                if not isinstance(raw_expr, dict):
                    msg = "Invalid expr payload in tactic argument."
                    raise ValueError(msg)
                return cast(
                    TacticArg,
                    ExprSerializer.from_dict(
                        cast(dict[str, JsonValue], raw_expr)
                    ),
                )
            if kind == "tuple":
                raw_items = value.get("items")
                if not isinstance(raw_items, list):
                    msg = "Invalid tuple payload in tactic argument."
                    raise ValueError(msg)
                return cast(
                    TacticArg,
                    tuple(
                        TacticPlanSerializer.decode_arg(item)
                        for item in raw_items
                    ),
                )
            if kind == "set":
                raw_items = value.get("items")
                if not isinstance(raw_items, list):
                    msg = "Invalid set payload in tactic argument."
                    raise ValueError(msg)
                decoded_items = [
                    TacticPlanSerializer.decode_arg(item)
                    for item in raw_items
                ]
                if any(not isinstance(item, str) for item in decoded_items):
                    msg = "set tactic argument must contain only strings."
                    raise ValueError(msg)
                return cast(
                    TacticArg,
                    {cast(str, item) for item in decoded_items}
                )
            msg = f"Unknown tactic argument kind: {kind}"
            raise ValueError(msg)

        if value is None or isinstance(value, str):
            return value
        if type(value) is int:
            return value
        msg = f"Unsupported tactic argument value: {value!r}"
        raise ValueError(msg)

    @classmethod
    def to_dict(cls, plan: TacticPlan) -> dict[str, JsonValue]:
        """Convert a TacticPlan instance into a JSON-safe dictionary."""
        tactic, args = plan
        return {
            "tactic": tactic,
            "args": {
                key: cls.encode_arg(value) for key, value in args.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, JsonValue]) -> TacticPlan:
        """Convert a dictionary into a TacticPlan instance."""
        if "tactic" not in data:
            msg = "Missing 'tactic' key in TacticPlan data."
            raise ValueError(msg)
        if "args" not in data:
            msg = "Missing 'args' key in TacticPlan data."
            raise ValueError(msg)

        tactic = data["tactic"]
        if not isinstance(tactic, str):
            msg = "Tactic name must be a string."
            raise ValueError(msg)
        raw_args = data["args"]
        if not isinstance(raw_args, dict):
            msg = "Tactic args must be a dictionary."
            raise ValueError(msg)

        args = {
            key: cast(TacticArg, cls.decode_arg(cast(JsonValue, value)))
            for key, value in raw_args.items()
        }

        return (tactic, args)
