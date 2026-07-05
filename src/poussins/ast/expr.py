"""
Unified expression AST nodes.

This module defines a single Expr hierarchy that represents both data terms and
proposition-level expressions (Prop-valued expressions), closer to Lean/Coq's
single core syntax tree model.
"""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

Sort = str


class Expr(ABC):
    pass


@dataclass(frozen=True)
class EVar(Expr):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class EApp(Expr):
    name: str
    args: tuple[Expr, ...]

    def __init__(self, name: str, args: list[Expr] | tuple[Expr, ...]):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "args", tuple(args))

    def __str__(self) -> str:
        if not self.args:
            return self.name
        rendered_args = ", ".join(str(arg) for arg in self.args)
        return f"{self.name}({rendered_args})"


@dataclass(frozen=True)
class EEq(Expr):
    left: Expr
    right: Expr

    @property
    def sort(self) -> Sort:
        return "Prop"

    def __str__(self) -> str:
        return f"({self.left} = {self.right})"


@dataclass(frozen=True)
class EImp(Expr):
    antecedent: Expr
    consequent: Expr

    @property
    def sort(self) -> Sort:
        return "Prop"

    def __str__(self) -> str:
        return f"({self.antecedent} -> {self.consequent})"


@dataclass(frozen=True)
class EAnd(Expr):
    left: Expr
    right: Expr

    @property
    def sort(self) -> Sort:
        return "Prop"

    def __str__(self) -> str:
        return f"({self.left} /\\ {self.right})"


@dataclass(frozen=True)
class EOr(Expr):
    left: Expr
    right: Expr

    @property
    def sort(self) -> Sort:
        return "Prop"

    def __str__(self) -> str:
        return f"({self.left} \\/ {self.right})"


@dataclass(frozen=True)
class ETop(Expr):
    @property
    def sort(self) -> Sort:
        return "Prop"

    def __str__(self) -> str:
        return "Top"


@dataclass(frozen=True)
class EBot(Expr):
    @property
    def sort(self) -> Sort:
        return "Prop"

    def __str__(self) -> str:
        return "Bot"


@dataclass(frozen=True)
class EForall(Expr):
    var: str
    sort: Sort
    body: Expr

    def __str__(self) -> str:
        return f"forall {self.var}: {self.sort}, {self.body}"


@dataclass(frozen=True)
class EExists(Expr):
    var: str
    sort: Sort
    body: Expr

    def __str__(self) -> str:
        return f"exists {self.var}: {self.sort}, {self.body}"


@dataclass(frozen=True)
class FunctionSymbol:
    name: str
    arg_sorts: tuple[Sort, ...]
    result_sort: Sort

    def __init__(self, name: str, arg_sorts: list[Sort] | tuple[Sort, ...], result_sort: Sort):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "arg_sorts", tuple(arg_sorts))
        object.__setattr__(self, "result_sort", result_sort)
