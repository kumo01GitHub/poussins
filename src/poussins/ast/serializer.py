"""Serialization and deserialization of AST nodes for expressions."""
from __future__ import annotations

import json
from typing import cast

from .expr import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
)
from .universe import (
    UnivLevel,
    UnivLevelIMax,
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)


class UnivLevelSerializer:
    """Serializes and deserializes UnivLevel instances."""

    @classmethod
    def to_dict(cls, level: UnivLevel) -> dict:
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
                    "name": name
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
    def from_dict(cls, data: dict) -> UnivLevel:
        """Convert a dictionary into a UnivLevel instance."""
        match data["type"]:
            case "UnivLevelZero":
                return UnivLevelZero()
            case "UnivLevelSucc":
                return UnivLevelSucc(cls.from_dict(data["pred"]))
            case "UnivLevelParam":
                return UnivLevelParam(cast(str, data["name"]))
            case "UnivLevelMax":
                return UnivLevelMax(
                    cls.from_dict(data["left"]),
                    cls.from_dict(data["right"]),
                )
            case "UnivLevelIMax":
                lhs_data = cast(dict, data["lhs"])
                rhs_data = cast(dict, data["rhs"])
                return UnivLevelIMax(
                    cls.from_dict(lhs_data),
                    cls.from_dict(rhs_data),
                )
            case _:
                raise ValueError(
                    f"Unknown UnivLevel type: {data.get('type')}"
                )

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
    def to_dict(cls, expr: Expr) -> dict:
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
                    "name": name
                }
            case EConst(name, levels):
                return {
                    "type": "EConst",
                    "name": name,
                    "levels": [UnivLevelSerializer.to_dict(lv) for lv in levels],
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
                    "goal_id": goal_id
                }

    @classmethod
    def from_dict(cls, data: dict) -> Expr:
        """Convert a dictionary into an Expr instance."""
        match data.get("type"):
            case "ESort":
                level_data = cast(dict, data["level"])
                return ESort(UnivLevelSerializer.from_dict(level_data))
            case "EVar":
                return EVar(cast(str, data["name"]))
            case "EConst":
                levels_data = cast(list[dict], data["levels"])
                return EConst(
                    name=cast(str, data["name"]),
                    levels=tuple(
                        UnivLevelSerializer.from_dict(lv) for lv in levels_data
                    ),
                )
            case "EPi":
                return EPi(
                    var=cast(str, data["var"]),
                    domain=cls.from_dict(cast(dict, data["domain"])),
                    body=cls.from_dict(cast(dict, data["body"])),
                )
            case "ELam":
                return ELam(
                    var=cast(str, data["var"]),
                    domain=cls.from_dict(cast(dict, data["domain"])),
                    body=cls.from_dict(cast(dict, data["body"])),
                )
            case "EApp":
                return EApp(
                    fn=cls.from_dict(cast(dict, data["fn"])),
                    arg=cls.from_dict(cast(dict, data["arg"])),
                )
            case "EMatch":
                cases_data = cast(list[dict], data["cases"])
                return EMatch(
                    inductive_name=cast(str, data["inductive_name"]),
                    discriminee=cls.from_dict(
                        cast(dict, data["discriminee"])
                    ),
                    motive=cls.from_dict(cast(dict, data["motive"])),
                    cases=tuple(cls.from_dict(c) for c in cases_data),
                )
            case "EMetaVar":
                return EMetaVar(cast(str, data["goal_id"]))
            case _:
                raise ValueError(f"Unknown Expr type: {data.get('type')}")

    @classmethod
    def serialize(cls, expr: Expr) -> str:
        """Serialize an Expr instance into a JSON string."""
        return json.dumps(cls.to_dict(expr))

    @classmethod
    def deserialize(cls, json_str: str) -> Expr:
        """Deserialize a JSON string into an Expr instance."""
        return cls.from_dict(json.loads(json_str))
