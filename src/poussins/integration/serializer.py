"""Serialization and deserialization helpers for AST and tactic plans."""
from __future__ import annotations

import json
from typing import cast

from ..ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
    UnivLevel,
    UnivLevelIMax,
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)
from .tactic import TacticArg, TacticPlan

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


class UnivLevelSerializer:
    """Serializes and deserializes UnivLevel instances."""

    @classmethod
    def to_dict(cls, level: UnivLevel) -> dict[str, JsonValue]:
        """Convert a UnivLevel instance into a dictionary."""
        match level:
            case UnivLevelZero():
                return {"type": "UnivLevelZero"}
            case UnivLevelSucc(pred):
                return {
                    "type": "UnivLevelSucc",
                    "pred": cls.to_dict(pred),
                }
            case UnivLevelParam(name):
                return {
                    "type": "UnivLevelParam",
                    "name": name,
                }
            case UnivLevelMax(left, right):
                return {
                    "type": "UnivLevelMax",
                    "left": cls.to_dict(left),
                    "right": cls.to_dict(right),
                }
            case UnivLevelIMax(left, right):
                return {
                    "type": "UnivLevelIMax",
                    "left": cls.to_dict(left),
                    "right": cls.to_dict(right),
                }

    @classmethod
    def from_dict(cls, data: dict[str, JsonValue]) -> UnivLevel:
        """Convert a dictionary into a UnivLevel instance."""
        match data.get("type"):
            case "UnivLevelZero":
                return UnivLevelZero()
            case "UnivLevelSucc":
                pred_data = cast(dict[str, JsonValue], data["pred"])
                return UnivLevelSucc(cls.from_dict(pred_data))
            case "UnivLevelParam":
                return UnivLevelParam(cast(str, data["name"]))
            case "UnivLevelMax":
                left_data = cast(dict[str, JsonValue], data["left"])
                right_data = cast(dict[str, JsonValue], data["right"])
                return UnivLevelMax(
                    cls.from_dict(left_data),
                    cls.from_dict(right_data),
                )
            case "UnivLevelIMax":
                lhs_data = cast(
                    dict[str, JsonValue],
                    data.get("left", data.get("lhs")),
                )
                rhs_data = cast(
                    dict[str, JsonValue],
                    data.get("right", data.get("rhs")),
                )
                return UnivLevelIMax(
                    cls.from_dict(lhs_data),
                    cls.from_dict(rhs_data),
                )
            case _:
                msg = f"Unknown UnivLevel type: {data.get('type')}"
                raise ValueError(msg)

    @classmethod
    def serialize(cls, level: UnivLevel) -> str:
        """Serialize a UnivLevel instance into a JSON string."""
        return json.dumps(cls.to_dict(level))

    @classmethod
    def deserialize(cls, json_str: str) -> UnivLevel:
        """Deserialize a JSON string into a UnivLevel instance."""
        return cls.from_dict(json.loads(json_str))


class ExprSerializer:
    """Serializes and deserializes Expr instances."""

    @classmethod
    def to_dict(cls, expr: Expr) -> dict[str, JsonValue]:
        """Convert an Expr instance into a dictionary."""
        match expr:
            case ESort(level):
                return {
                    "type": "ESort",
                    "level": UnivLevelSerializer.to_dict(level),
                }
            case EVar(name):
                return {
                    "type": "EVar",
                    "name": name,
                }
            case EConst(name, levels):
                return {
                    "type": "EConst",
                    "name": name,
                    "levels": [
                        UnivLevelSerializer.to_dict(lv) for lv in levels
                    ],
                }
            case EPi(var, domain, body):
                return {
                    "type": "EPi",
                    "var": var,
                    "domain": cls.to_dict(domain),
                    "body": cls.to_dict(body),
                }
            case ELam(var, domain, body):
                return {
                    "type": "ELam",
                    "var": var,
                    "domain": cls.to_dict(domain),
                    "body": cls.to_dict(body),
                }
            case EApp(fn, arg):
                return {
                    "type": "EApp",
                    "fn": cls.to_dict(fn),
                    "arg": cls.to_dict(arg),
                }
            case EMatch(inductive_name, discriminee, motive, cases):
                return {
                    "type": "EMatch",
                    "inductive_name": inductive_name,
                    "discriminee": cls.to_dict(discriminee),
                    "motive": cls.to_dict(motive),
                    "cases": [cls.to_dict(case) for case in cases],
                }
            case EMetaVar(goal_id):
                return {
                    "type": "EMetaVar",
                    "goal_id": goal_id,
                }

    @classmethod
    def from_dict(cls, data: dict[str, JsonValue]) -> Expr:
        """Convert a dictionary into an Expr instance."""
        match data.get("type"):
            case "ESort":
                level_data = cast(dict[str, JsonValue], data["level"])
                return ESort(UnivLevelSerializer.from_dict(level_data))
            case "EVar":
                return EVar(cast(str, data["name"]))
            case "EConst":
                levels_data = cast(list[dict[str, JsonValue]], data["levels"])
                return EConst(
                    name=cast(str, data["name"]),
                    levels=tuple(
                        UnivLevelSerializer.from_dict(lv) for lv in levels_data
                    ),
                )
            case "EPi":
                return EPi(
                    var=cast(str, data["var"]),
                    domain=cls.from_dict(
                        cast(dict[str, JsonValue], data["domain"])
                    ),
                    body=cls.from_dict(cast(dict[str, JsonValue], data["body"])),
                )
            case "ELam":
                return ELam(
                    var=cast(str, data["var"]),
                    domain=cls.from_dict(
                        cast(dict[str, JsonValue], data["domain"])
                    ),
                    body=cls.from_dict(cast(dict[str, JsonValue], data["body"])),
                )
            case "EApp":
                return EApp(
                    fn=cls.from_dict(cast(dict[str, JsonValue], data["fn"])),
                    arg=cls.from_dict(cast(dict[str, JsonValue], data["arg"])),
                )
            case "EMatch":
                cases_data = cast(
                    list[dict[str, JsonValue]], data["cases"]
                )
                return EMatch(
                    inductive_name=cast(str, data["inductive_name"]),
                    discriminee=cls.from_dict(
                        cast(dict[str, JsonValue], data["discriminee"])
                    ),
                    motive=cls.from_dict(
                        cast(dict[str, JsonValue], data["motive"])
                    ),
                    cases=tuple(cls.from_dict(c) for c in cases_data),
                )
            case "EMetaVar":
                return EMetaVar(cast(str, data["goal_id"]))
            case _:
                msg = f"Unknown Expr type: {data.get('type')}"
                raise ValueError(msg)

    @classmethod
    def serialize(cls, expr: Expr) -> str:
        """Serialize an Expr instance into a JSON string."""
        return json.dumps(cls.to_dict(expr))

    @classmethod
    def deserialize(cls, json_str: str) -> Expr:
        """Deserialize a JSON string into an Expr instance."""
        return cls.from_dict(json.loads(json_str))


class TacticPlanSerializer:
    """Serializes and deserializes TacticPlan instances."""

    @staticmethod
    def encode_arg(value: TacticArg) -> JsonValue:
        """Encode tactic argument values into JSON-safe tagged structures."""
        if isinstance(value, list):
            return [
                TacticPlanSerializer.encode_arg(cast(TacticArg, item))
                for item in value
            ]
        if isinstance(value, frozenset):
            return {
                "__kind": "frozenset",
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
            if kind == "frozenset":
                raw_items = value.get("items")
                if not isinstance(raw_items, list):
                    msg = "Invalid frozenset payload in tactic argument."
                    raise ValueError(msg)
                decoded_items = [
                    TacticPlanSerializer.decode_arg(item)
                    for item in raw_items
                ]
                if any(not isinstance(item, str) for item in decoded_items):
                    msg = "frozenset tactic argument must contain only strings."
                    raise ValueError(msg)
                return cast(
                    TacticArg,
                    frozenset(cast(str, item) for item in decoded_items),
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

    @classmethod
    def serialize(cls, plan: TacticPlan) -> str:
        """Serialize a TacticPlan instance into a JSON string."""
        return json.dumps(cls.to_dict(plan))

    @classmethod
    def deserialize(cls, json_str: str) -> TacticPlan:
        """Deserialize a JSON string into a TacticPlan instance."""
        return cls.from_dict(json.loads(json_str))
