"""Serialization and deserialization of AST nodes for expressions."""
from __future__ import annotations

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
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)

type SerializedExpr = dict[str, object]
type SerializedUnivLevel = dict[str, object]


class UnivLevelSerializer:
    """Serializes and deserializes UnivLevel instances."""

    @classmethod
    def serialize(cls, level: UnivLevel) -> SerializedUnivLevel:
        """Serialize a UnivLevel instance into a dictionary."""
        match level:
            case UnivLevelZero():
                return {"type": "UnivLevelZero"}
            case UnivLevelSucc(pred):
                return {
                    "type": "UnivLevelSucc",
                    "pred": cls.serialize(pred),
                }
            case UnivLevelMax(lhs, rhs):
                return {
                    "type": "UnivLevelMax",
                    "lhs": cls.serialize(lhs),
                    "rhs": cls.serialize(rhs),
                }
            case UnivLevelParam(name):
                return {"type": "UnivLevelParam", "name": name}
            case _:
                raise NotImplementedError(
                    f"Unsupported UnivLevel type: {type(level)}"
                )

    @classmethod
    def deserialize(cls, data: SerializedUnivLevel) -> UnivLevel:
        """Deserialize a dictionary into a UnivLevel instance."""
        match data.get("type"):
            case "UnivLevelZero":
                return UnivLevelZero()
            case "UnivLevelSucc":
                pred_data = cast(SerializedUnivLevel, data["pred"])
                return UnivLevelSucc(cls.deserialize(pred_data))
            case "UnivLevelMax":
                lhs_data = cast(SerializedUnivLevel, data["lhs"])
                rhs_data = cast(SerializedUnivLevel, data["rhs"])
                return UnivLevelMax(
                    cls.deserialize(lhs_data),
                    cls.deserialize(rhs_data),
                )
            case "UnivLevelParam":
                return UnivLevelParam(cast(str, data["name"]))
            case _:
                raise ValueError(
                    f"Unknown UnivLevel type: {data.get('type')}"
                )


class ExprSerializer:
    """Serializes and deserializes Expr instances."""

    @classmethod
    def serialize(cls, expr: Expr) -> SerializedExpr:
        """Serialize an Expr instance into a dictionary."""
        match expr:
            case ESort(level):
                return {
                    "type": "ESort",
                    "level": UnivLevelSerializer.serialize(level),
                }
            case EVar(name):
                return {"type": "EVar", "name": name}
            case EConst(name, levels):
                return {
                    "type": "EConst",
                    "name": name,
                    "levels": [UnivLevelSerializer.serialize(lv) for lv in levels],
                }
            case EPi(var, domain, body):
                return {
                    "type": "EPi",
                    "var": var,
                    "domain": cls.serialize(domain),
                    "body": cls.serialize(body),
                }
            case ELam(var, domain, body):
                return {
                    "type": "ELam",
                    "var": var,
                    "domain": cls.serialize(domain),
                    "body": cls.serialize(body),
                }
            case EApp(fn, arg):
                return {
                    "type": "EApp",
                    "fn": cls.serialize(fn),
                    "arg": cls.serialize(arg),
                }
            case EMatch(inductive_name, discriminee, motive, cases):
                return {
                    "type": "EMatch",
                    "inductive_name": inductive_name,
                    "discriminee": cls.serialize(discriminee),
                    "motive": cls.serialize(motive),
                    "cases": [cls.serialize(c) for c in cases],
                }
            case EMetaVar(goal_id):
                return {"type": "EMetaVar", "goal_id": goal_id}
            case _:
                raise NotImplementedError(f"Unsupported Expr type: {type(expr)}")

    @classmethod
    def deserialize(cls, data: SerializedExpr) -> Expr:
        """Deserialize a dictionary into an Expr instance."""
        match data.get("type"):
            case "ESort":
                level_data = cast(SerializedUnivLevel, data["level"])
                return ESort(UnivLevelSerializer.deserialize(level_data))
            case "EVar":
                return EVar(cast(str, data["name"]))
            case "EConst":
                levels_data = cast(list[SerializedUnivLevel], data["levels"])
                return EConst(
                    name=cast(str, data["name"]),
                    levels=tuple(
                        UnivLevelSerializer.deserialize(lv) for lv in levels_data
                    ),
                )
            case "EPi":
                return EPi(
                    var=cast(str, data["var"]),
                    domain=cls.deserialize(
                        cast(SerializedExpr, data["domain"])
                    ),
                    body=cls.deserialize(cast(SerializedExpr, data["body"])),
                )
            case "ELam":
                return ELam(
                    var=cast(str, data["var"]),
                    domain=cls.deserialize(
                        cast(SerializedExpr, data["domain"])
                    ),
                    body=cls.deserialize(cast(SerializedExpr, data["body"])),
                )
            case "EApp":
                return EApp(
                    fn=cls.deserialize(cast(SerializedExpr, data["fn"])),
                    arg=cls.deserialize(cast(SerializedExpr, data["arg"])),
                )
            case "EMatch":
                cases_data = cast(list[SerializedExpr], data["cases"])
                return EMatch(
                    inductive_name=cast(str, data["inductive_name"]),
                    discriminee=cls.deserialize(
                        cast(SerializedExpr, data["discriminee"])
                    ),
                    motive=cls.deserialize(
                        cast(SerializedExpr, data["motive"])
                    ),
                    cases=tuple(cls.deserialize(c) for c in cases_data),
                )
            case "EMetaVar":
                return EMetaVar(cast(str, data["goal_id"]))
            case _:
                raise ValueError(
                    f"Unknown Expr type: {data.get('type')}"
                )
