from __future__ import annotations

from collections.abc import Sequence
from typing import TypeAlias

class UnivLevelZero:
    pass

class UnivLevelSucc:
    pred: UnivLevel

class UnivLevelParam:
    name: str

class UnivLevelMax:
    left: UnivLevel
    right: UnivLevel

class UnivLevelIMax:
    left: UnivLevel
    right: UnivLevel

UnivLevel: TypeAlias = UnivLevelZero | UnivLevelSucc | UnivLevelParam | UnivLevelMax | UnivLevelIMax

class ESort:
    level: UnivLevel

class EFVar:
    name: str

class EBVar:
    idx: int

class EConst:
    name: str
    levels: list[UnivLevel]

class EApp:
    f: Expr
    arg: Expr

class ELam:
    var: str
    t: Expr
    body: Expr

class EPi:
    var: str
    t: Expr
    body: Expr

class ELet:
    var: str
    t: Expr
    value: Expr
    body: Expr

class ELit:
    lit: Literal

class EMVar:
    id: str

Literal: TypeAlias = int | float | str | list[Expr]
Expr: TypeAlias = ESort | EFVar | EBVar | EConst | EApp | ELam | EPi | ELet | ELit | EMVar

def univ_level(level: int | str | UnivLevel) -> UnivLevel: ...
def univ_levels(levels: Sequence[int | str | UnivLevel]) -> tuple[UnivLevel, ...]: ...
def univ_level_max(*levels: int | str | UnivLevel) -> UnivLevel: ...
def univ_level_imax(left: int | str | UnivLevel, right: int | str | UnivLevel) -> UnivLevel: ...
def sort(level: int | str | UnivLevel) -> ESort: ...
def var(name: str) -> EFVar: ...
def free_var(name: str) -> EFVar: ...
def app(fn: Expr | str, *args: Expr | str) -> Expr: ...
def lam(binders: Sequence[tuple[str, Expr | str]], body: Expr | str) -> ELam: ...
def let_(var_name: str, var_type: Expr | str, value: Expr | str, body: Expr | str) -> ELet: ...
def pi(binders: Sequence[tuple[str, Expr | str]], body: Expr | str) -> EPi: ...
def const_(env: object, name: str) -> EConst: ...

__all__ = [
    "Expr",
    "Literal",
    "UnivLevel",
    "UnivLevelZero",
    "UnivLevelSucc",
    "UnivLevelParam",
    "UnivLevelMax",
    "UnivLevelIMax",
    "ESort",
    "EFVar",
    "EBVar",
    "EConst",
    "EApp",
    "ELam",
    "EPi",
    "ELet",
    "ELit",
    "EMVar",
    "univ_level",
    "univ_levels",
    "univ_level_max",
    "univ_level_imax",
    "sort",
    "var",
    "free_var",
    "app",
    "lam",
    "let_",
    "pi",
    "const_",
]
