"""Module for serializing and deserializing objects to and from JSON."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


class Serializer[T](ABC):
    """Abstract base class for serializers."""

    @classmethod
    @abstractmethod
    def to_dict(cls, obj: T) -> dict[str, JsonValue]:
        """Convert an object into a dictionary."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, JsonValue]) -> T:
        """Convert a dictionary into an object."""
        pass

    @classmethod
    def serialize(cls, obj: T) -> str:
        """Serialize an object into a JSON string."""
        return json.dumps(cls.to_dict(obj))

    @classmethod
    def deserialize(cls, json_str: str) -> T:
        """Deserialize a JSON string into an object."""
        return cls.from_dict(json.loads(json_str))
