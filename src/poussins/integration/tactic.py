"""Tactic plan schemas and serialization helpers."""
from __future__ import annotations

from ..ast import Expr

type TacticArg = str | int | list[str] | frozenset[str] | tuple | Expr | None
type TacticPlan = tuple[str, dict[str, TacticArg]]
