"""Core expression data types for the proof assistant."""
from __future__ import annotations

from dataclasses import dataclass
from typing import override

from .universe import UnivLevel, UnivLevelParam, UnivLevelSucc, UnivLevelZero


@dataclass(frozen=True)
class ESort:
    """Sort, e.g. Prop, Type u, etc."""

    level: UnivLevel

    @override
    def __str__(self) -> str:
        match self.level:
            case UnivLevelZero():
                return "Prop"
            case UnivLevelSucc(pred):
                depth = 1
                current = pred
                while isinstance(current, UnivLevelSucc):
                    depth += 1
                    current = current.pred
                if isinstance(current, UnivLevelZero):
                    return f"Type {depth - 1}"
                elif isinstance(current, UnivLevelParam):
                    return f"Sort({current.name} + {depth})"
                else:
                    return f"Sort({self.level})"
            case _:
                return f"Sort({self.level})"


@dataclass(frozen=True)
class EFVar:
    """Free variable, e.g. x, y."""

    name: str

    @override
    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class EBVar:
    """Bound variable represented by de Bruijn index."""

    index: int

    @override
    def __str__(self) -> str:
        return f"#{self.index}"


@dataclass(frozen=True)
class EConst:
    """Constant, e.g. nat, list, etc."""

    name: str
    levels: tuple[UnivLevel, ...]

    @override
    def __str__(self) -> str:
        if self.levels:
            levels_str = ", ".join(str(lv) for lv in self.levels)
            return f"{self.name}.{{{levels_str}}}"
        else:
            return self.name


@dataclass(frozen=True)
class EPi:
    """Dependent product (Π-type), e.g. Π x : A, B."""

    var: str
    domain: Expr
    body: Expr

    @override
    def __str__(self) -> str:
        return f"(Π {self.var} : {self.domain}, {self.body})"


@dataclass(frozen=True)
class ELam:
    """Lambda abstraction, e.g. λ x : A, b."""

    var: str
    domain: Expr
    body: Expr

    @override
    def __str__(self) -> str:
        return f"(λ {self.var} : {self.domain}, {self.body})"


@dataclass(frozen=True)
class EApp:
    """Application, e.g. f a."""

    fn: Expr
    arg: Expr

    @override
    def __str__(self) -> str:
        return f"({self.fn} {self.arg})"


@dataclass(frozen=True)
class ELet:
    """Local let-binding, e.g. let x : T := v in b."""

    var: str
    type: Expr
    value: Expr
    body: Expr

    @override
    def __str__(self) -> str:
        return f"(let {self.var} : {self.type} := {self.value} in {self.body})"


@dataclass(frozen=True)
class EMetaVar:
    """Meta-variable, e.g. ?m."""

    goal_id: str

    @override
    def __str__(self) -> str:
        return f"?{self.goal_id}"


Expr = (
    ESort
    | EFVar
    | EBVar
    | EConst
    | EPi
    | ELam
    | EApp
    | ELet
    | EMetaVar
)
