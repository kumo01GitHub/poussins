from __future__ import annotations

from collections.abc import Sequence

class UnivLevelZero:
    pass

class UnivLevelSucc:
    @property
    def pred(self) -> UnivLevel: ...

class UnivLevelParam:
    @property
    def name(self) -> str: ...

class UnivLevelMax:
    @property
    def left(self) -> UnivLevel: ...
    @property
    def right(self) -> UnivLevel: ...

class UnivLevelIMax:
    @property
    def left(self) -> UnivLevel: ...
    @property
    def right(self) -> UnivLevel: ...

type UnivLevel = (
    UnivLevelZero
    | UnivLevelSucc
    | UnivLevelParam
    | UnivLevelMax
    | UnivLevelIMax
)

class ESort:
    @property
    def level(self) -> UnivLevel: ...

class EFVar:
    @property
    def name(self) -> str: ...

class EBVar:
    @property
    def idx(self) -> int: ...

class EConst:
    @property
    def name(self) -> str: ...
    @property
    def levels(self) -> list[UnivLevel]: ...

class EApp:
    @property
    def f(self) -> Expr: ...
    @property
    def arg(self) -> Expr: ...

class ELam:
    @property
    def var(self) -> str: ...
    @property
    def t(self) -> Expr: ...
    @property
    def body(self) -> Expr: ...

class EPi:
    @property
    def var(self) -> str: ...
    @property
    def t(self) -> Expr: ...
    @property
    def body(self) -> Expr: ...

class ELet:
    @property
    def var(self) -> str: ...
    @property
    def t(self) -> Expr: ...
    @property
    def value(self) -> Expr: ...
    @property
    def body(self) -> Expr: ...

class ELit:
    @property
    def lit(self) -> Literal: ...

class EMVar:
    @property
    def id(self) -> str: ...

type Literal = int | float | str | list[Expr]
type Expr = ESort | EFVar | EBVar | EConst | EApp | ELam | EPi | ELet | ELit | EMVar

def univ_level(level: int | str | UnivLevel) -> UnivLevel: ...
def univ_levels(levels: Sequence[int | str | UnivLevel]) -> tuple[UnivLevel, ...]: ...
def univ_level_max(*levels: int | str | UnivLevel) -> UnivLevel: ...
def univ_level_imax(
    left: int | str | UnivLevel,
    right: int | str | UnivLevel
) -> UnivLevel: ...
def sort(level: int | str | UnivLevel) -> ESort: ...
def var(name: str) -> EFVar: ...
def free_var(name: str) -> EFVar: ...
def app(fn: Expr | str, *args: Expr | str) -> Expr: ...
def lam(binders: Sequence[tuple[str, Expr | str]], body: Expr | str) -> ELam: ...
def let_(
    var_name: str,
    var_type: Expr | str,
    value: Expr | str,
    body: Expr | str
) -> ELet: ...
def pi(binders: Sequence[tuple[str, Expr | str]], body: Expr | str) -> EPi: ...
def const_(env: object, name: str) -> EConst: ...

class Goal:
    @property
    def id(self) -> str: ...
    @property
    def statement(self) -> Expr: ...
    @property
    def local_context(self) -> list[tuple[str, Expr]]: ...

    def has_local_hypothesis(self, name: str) -> bool: ...
    def get_local_hypothesis(self, name: str) -> Expr | None: ...
    def __hash__(self) -> int: ...

__all__ = [
    # AST classes
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
    # Builder functions
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
    # Goal class
    "Goal",
]
