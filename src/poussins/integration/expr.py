"""Module for serializing and deserializing AST nodes to and from JSON."""
from __future__ import annotations

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
from .serializer import JsonValue, Serializer


class UnivLevelSerializer(Serializer[UnivLevel]):
    """Serializes and deserializes UnivLevel instances."""

    @classmethod
    def to_dict(cls, obj: UnivLevel) -> dict[str, JsonValue]:
        """Convert a UnivLevel instance into a dictionary."""
        match obj:
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


class ExprSerializer(Serializer[Expr]):
    """Serializes and deserializes Expr instances."""

    @classmethod
    def to_dict(cls, obj: Expr) -> dict[str, JsonValue]:
        """Convert an Expr instance into a dictionary."""
        match obj:
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
