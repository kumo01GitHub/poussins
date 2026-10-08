"""Tactic plan schemas and serialization helpers."""
from __future__ import annotations

from ..ast import Expr
from ..framework.proof_script import ExprLike

type TacticArg = str | int | list[str] | set[str] | tuple | Expr | ExprLike| None
type TacticPlan = tuple[str, dict[str, TacticArg]]
