"""Serializers for the environment module."""
from __future__ import annotations

from typing import cast

from ..ast import ExprSerializer
from ..utils.serializer import JsonValue, Serializer
from .declaration import (
    AxiomDeclaration,
    ConstructorDeclaration,
    Declaration,
    DefinitionDeclaration,
    InductiveDeclaration,
    QuotDeclaration,
    RecursorDeclaration,
    TheoremDeclaration,
)


class DeclarationSerializer(Serializer[Declaration]):
    """Serializes and deserializes Declaration instances."""

    @classmethod
    def to_dict(cls, obj: Declaration) -> dict[str, JsonValue]:
        """Convert a Declaration instance into a dictionary."""
        if isinstance(obj, AxiomDeclaration):
            return {
                "__kind": "axiom",
                "name": obj.name,
                "level_params": list(obj.level_params),
                "type": ExprSerializer.to_dict(obj.type),
            }
        elif isinstance(obj, DefinitionDeclaration):
            return {
                "__kind": "definition",
                "name": obj.name,
                "level_params": list(obj.level_params),
                "type": ExprSerializer.to_dict(obj.type),
                "value": ExprSerializer.to_dict(obj.value),
            }
        elif isinstance(obj, TheoremDeclaration):
            return {
                "__kind": "theorem",
                "name": obj.name,
                "level_params": list(obj.level_params),
                "type": ExprSerializer.to_dict(obj.type),
                "value": ExprSerializer.to_dict(obj.value),
            }
        elif isinstance(obj, InductiveDeclaration):
            return {
                "__kind": "inductive",
                "name": obj.name,
                "level_params": list(obj.level_params),
                "type": ExprSerializer.to_dict(obj.type),
                "constructor_names": list(obj.constructor_names),
            }
        elif isinstance(obj, ConstructorDeclaration):
            return {
                "__kind": "constructor",
                "name": obj.name,
                "level_params": list(obj.level_params),
                "type": ExprSerializer.to_dict(obj.type),
                "inductive_name": obj.inductive_name,
            }
        elif isinstance(obj, RecursorDeclaration):
            return {
                "__kind": "recursor",
                "name": obj.name,
                "level_params": list(obj.level_params),
                "type": ExprSerializer.to_dict(obj.type),
                "inductive_name": obj.inductive_name,
                "num_params": obj.num_params,
                "num_indices": obj.num_indices,
                "num_minors": obj.num_minors,
            }
        elif isinstance(obj, QuotDeclaration):
            return {
                "__kind": "quot",
                "name": obj.name,
                "level_params": list(obj.level_params),
                "type": ExprSerializer.to_dict(obj.type),
                "variant": obj.variant,
            }
        else:
            raise ValueError(f"Unsupported Declaration type: {type(obj)}")

    @classmethod
    def from_dict(cls, data: dict[str, JsonValue]) -> Declaration:
        """Convert a dictionary into a Declaration instance."""
        kind = data.get("__kind")
        if kind == "axiom":
            return AxiomDeclaration(
                name=cast(str, data["name"]),
                level_params=cast(tuple[str, ...], data["level_params"]),
                type=ExprSerializer.from_dict(cast(dict[str, JsonValue], data["type"])),
            )
        elif kind == "definition":
            return DefinitionDeclaration(
                name=cast(str, data["name"]),
                level_params=cast(tuple[str, ...], data["level_params"]),
                type=ExprSerializer.from_dict(
                    cast(dict[str, JsonValue], data["type"])
                ),
                value=ExprSerializer.from_dict(
                    cast(dict[str, JsonValue], data["value"])
                ),
            )
        elif kind == "theorem":
            return TheoremDeclaration(
                name=cast(str, data["name"]),
                level_params=cast(tuple[str, ...], data["level_params"]),
                type=ExprSerializer.from_dict(
                    cast(dict[str, JsonValue], data["type"])
                ),
                value=ExprSerializer.from_dict(
                    cast(dict[str, JsonValue], data["value"])
                ),
            )
        elif kind == "inductive":
            return InductiveDeclaration(
                name=cast(str, data["name"]),
                level_params=cast(tuple[str, ...], data["level_params"]),
                type=ExprSerializer.from_dict(cast(dict[str, JsonValue], data["type"])),
                constructor_names=cast(tuple[str, ...], data["constructor_names"]),
            )
        elif kind == "constructor":
            return ConstructorDeclaration(
                name=cast(str, data["name"]),
                level_params=cast(tuple[str, ...], data["level_params"]),
                type=ExprSerializer.from_dict(cast(dict[str, JsonValue], data["type"])),
                inductive_name=cast(str, data["inductive_name"]),
            )
        elif kind == "recursor":
            return RecursorDeclaration(
                name=cast(str, data["name"]),
                level_params=cast(tuple[str, ...], data["level_params"]),
                type=ExprSerializer.from_dict(cast(dict[str, JsonValue], data["type"])),
                inductive_name=cast(str, data["inductive_name"]),
                num_params=cast(int, data["num_params"]),
                num_indices=cast(int, data["num_indices"]),
                num_minors=cast(int, data["num_minors"]),
            )
        elif kind == "quot":
            return QuotDeclaration(
                name=cast(str, data["name"]),
                level_params=cast(tuple[str, ...], data["level_params"]),
                type=ExprSerializer.from_dict(cast(dict[str, JsonValue], data["type"])),
                variant=cast(str, data["variant"]),
            )
        else:
            raise ValueError(f"Unsupported Declaration kind: {kind}")
