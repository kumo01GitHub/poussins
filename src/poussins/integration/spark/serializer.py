"""Serialization and deserialization utilities for ProofTaskNode instances."""
from __future__ import annotations

from typing import cast

from ...ast import (
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
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)
from ...errors import SparkIntegrationError
from .proof_task import ProofTaskNode, TacticRecipeItem

type SerializedExpr = dict[str, object]
type SerializedNodeDict = dict[
    str, str | SerializedExpr | list[TacticRecipeItem] | list[str]
]


class ProofTaskSerializer:
    """Serializes and deserializes ProofTaskNode instances."""

    # -------------------------------------------------------------------------
    # UnivLevel AST Serialization
    # -------------------------------------------------------------------------
    @classmethod
    def serialize_univ_level(cls, level: UnivLevel) -> dict[str, object]:
        """Serialize a UnivLevel instance into a dictionary."""
        match level:
            case UnivLevelZero():
                return {"type": "UnivLevelZero"}
            case UnivLevelSucc(pred):
                return {
                    "type": "UnivLevelSucc",
                    "pred": cls.serialize_univ_level(pred),
                }
            case UnivLevelMax(lhs, rhs):
                return {
                    "type": "UnivLevelMax",
                    "lhs": cls.serialize_univ_level(lhs),
                    "rhs": cls.serialize_univ_level(rhs),
                }
            case UnivLevelParam(name):
                return {"type": "UnivLevelParam", "name": name}
            case _:
                raise SparkIntegrationError(
                    f"Unsupported UnivLevel type: {type(level)}"
                )

    @classmethod
    def deserialize_univ_level(cls, data: dict[str, object]) -> UnivLevel:
        """Deserialize a dictionary into a UnivLevel instance."""
        match data.get("type"):
            case "UnivLevelZero":
                return UnivLevelZero()
            case "UnivLevelSucc":
                pred_data = cast(dict[str, object], data["pred"])
                return UnivLevelSucc(cls.deserialize_univ_level(pred_data))
            case "UnivLevelMax":
                lhs_data = cast(dict[str, object], data["lhs"])
                rhs_data = cast(dict[str, object], data["rhs"])
                return UnivLevelMax(
                    cls.deserialize_univ_level(lhs_data),
                    cls.deserialize_univ_level(rhs_data),
                )
            case "UnivLevelParam":
                return UnivLevelParam(cast(str, data["name"]))
            case _:
                raise SparkIntegrationError(
                    f"Unknown UnivLevel type: {data.get('type')}"
                )

    # -------------------------------------------------------------------------
    # Expr AST Serialization
    # -------------------------------------------------------------------------
    @classmethod
    def serialize_expr(cls, expr: Expr) -> SerializedExpr:
        """Serialize an Expr instance into a dictionary."""
        match expr:
            case ESort(level):
                return {
                    "type": "ESort",
                    "level": cls.serialize_univ_level(level),
                }
            case EVar(name):
                return {"type": "EVar", "name": name}
            case EConst(name, levels):
                return {
                    "type": "EConst",
                    "name": name,
                    "levels": [cls.serialize_univ_level(lv) for lv in levels],
                }
            case EPi(var, domain, body):
                return {
                    "type": "EPi",
                    "var": var,
                    "domain": cls.serialize_expr(domain),
                    "body": cls.serialize_expr(body),
                }
            case ELam(var, domain, body):
                return {
                    "type": "ELam",
                    "var": var,
                    "domain": cls.serialize_expr(domain),
                    "body": cls.serialize_expr(body),
                }
            case EApp(fn, arg):
                return {
                    "type": "EApp",
                    "fn": cls.serialize_expr(fn),
                    "arg": cls.serialize_expr(arg),
                }
            case EMatch(inductive_name, discriminee, motive, cases):
                return {
                    "type": "EMatch",
                    "inductive_name": inductive_name,
                    "discriminee": cls.serialize_expr(discriminee),
                    "motive": cls.serialize_expr(motive),
                    "cases": [cls.serialize_expr(c) for c in cases],
                }
            case EMetaVar(goal_id):
                return {"type": "EMetaVar", "goal_id": goal_id}
            case _:
                raise SparkIntegrationError(f"Unsupported Expr type: {type(expr)}")

    @classmethod
    def deserialize_expr(cls, data: SerializedExpr) -> Expr:
        """Deserialize a dictionary into an Expr instance."""
        match data.get("type"):
            case "ESort":
                level_data = cast(dict[str, object], data["level"])
                return ESort(cls.deserialize_univ_level(level_data))
            case "EVar":
                return EVar(cast(str, data["name"]))
            case "EConst":
                levels_data = cast(list[dict[str, object]], data["levels"])
                return EConst(
                    name=cast(str, data["name"]),
                    levels=tuple(
                        cls.deserialize_univ_level(lv) for lv in levels_data
                    ),
                )
            case "EPi":
                return EPi(
                    var=cast(str, data["var"]),
                    domain=cls.deserialize_expr(
                        cast(SerializedExpr, data["domain"])
                    ),
                    body=cls.deserialize_expr(cast(SerializedExpr, data["body"])),
                )
            case "ELam":
                return ELam(
                    var=cast(str, data["var"]),
                    domain=cls.deserialize_expr(
                        cast(SerializedExpr, data["domain"])
                    ),
                    body=cls.deserialize_expr(cast(SerializedExpr, data["body"])),
                )
            case "EApp":
                return EApp(
                    fn=cls.deserialize_expr(cast(SerializedExpr, data["fn"])),
                    arg=cls.deserialize_expr(cast(SerializedExpr, data["arg"])),
                )
            case "EMatch":
                cases_data = cast(list[SerializedExpr], data["cases"])
                return EMatch(
                    inductive_name=cast(str, data["inductive_name"]),
                    discriminee=cls.deserialize_expr(
                        cast(SerializedExpr, data["discriminee"])
                    ),
                    motive=cls.deserialize_expr(
                        cast(SerializedExpr, data["motive"])
                    ),
                    cases=tuple(cls.deserialize_expr(c) for c in cases_data),
                )
            case "EMetaVar":
                return EMetaVar(cast(str, data["goal_id"]))
            case _:
                raise SparkIntegrationError(
                    f"Unknown Expr type: {data.get('type')}"
                )

    # -------------------------------------------------------------------------
    # ProofTaskNode Serialization
    # -------------------------------------------------------------------------
    @classmethod
    def serialize_node(cls, node: ProofTaskNode) -> SerializedNodeDict:
        """Serialize a ProofTaskNode instance into a dictionary."""
        return {
            "name": node.name,
            "statement": cls.serialize_expr(node.statement),
            "tactic_recipe": node.tactic_recipe,
            "depends_on": node.depends_on,
        }

    @classmethod
    def deserialize_node(cls, data: SerializedNodeDict) -> ProofTaskNode:
        """Deserialize a dictionary into a ProofTaskNode instance."""
        return ProofTaskNode(
            name=cast(str, data["name"]),
            statement=cls.deserialize_expr(cast(SerializedExpr, data["statement"])),
            tactic_recipe=cast(list[TacticRecipeItem], data["tactic_recipe"]),
            depends_on=cast(list[str], data.get("depends_on", [])),
        )
