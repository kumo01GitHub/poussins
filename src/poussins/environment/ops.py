"""Operations on the environment."""
from __future__ import annotations

from ..ast import EConst, univ_levels
from .environment import Environment


def const(env: Environment, name: str) -> EConst:
    """Create an EConst expression for a declaration in the environment."""
    decl = env.get(name)
    if decl is None:
        raise ValueError(f"Declaration with name '{name}' does not exist in the environment.")

    return EConst(
        name=decl.name,
        levels=univ_levels(decl.level_params)
    )
