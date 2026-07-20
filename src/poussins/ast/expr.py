from __future__ import annotations
from abc import ABC
from dataclasses import dataclass

from .universe import UnivLevel, UnivLevelZero, UnivLevelSucc, UnivLevelParam


class Expr(ABC):
    """Abstract base class for expressions."""

    pass


@dataclass(frozen=True)
class ESort(Expr):
    """Sort, e.g. Prop, Type u, etc."""

    level: UnivLevel

    def __str__(self) -> str:
        match self.level:
            case UnivLevelZero():
                return "Prop"
            case UnivLevelSucc(UnivLevelZero()):
                return "Type"
            case UnivLevelSucc(pred):
                depth = 1
                current = pred
                while isinstance(current, UnivLevelSucc):
                    depth += 1
                    current = current.pred
                if isinstance(current, UnivLevelZero):
                    return f"Type {depth}"
                elif isinstance(current, UnivLevelParam):
                    return f"Sort({current.name} + {depth})"
                else:
                    return f"Sort({self.level})"
            case _:
                return f"Sort({self.level})"


@dataclass(frozen=True)
class EVar(Expr):
    """Variable, e.g. x, y."""

    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class EConst(Expr):
    """Constant, e.g. nat, list, etc."""

    name: str
    levels: tuple[UnivLevel, ...]

    def __str__(self) -> str:
        if self.levels:
            levels_str = ", ".join(str(l) for l in self.levels)
            return f"{self.name}.{{{levels_str}}}"
        else:
            return self.name


@dataclass(frozen=True)
class EPi(Expr):
    """Dependent product (Π-type), e.g. Π x : A, B."""

    var: str
    domain: Expr
    body: Expr

    def __str__(self) -> str:
        return f"(Π {self.var} : {self.domain}, {self.body})"


@dataclass(frozen=True)
class ELam(Expr):
    """Lambda abstraction, e.g. λ x : A, b."""

    var: str
    domain: Expr
    body: Expr

    def __str__(self) -> str:
        return f"(λ {self.var} : {self.domain}, {self.body})"


@dataclass(frozen=True)
class EApp(Expr):
    """Application, e.g. f a."""

    fn: Expr
    arg: Expr

    def __str__(self) -> str:
        return f"({self.fn} {self.arg})"


@dataclass(frozen=True)
class EMatch(Expr):
    """Pattern matching expression."""

    inductive_name: str
    discriminee: Expr
    motive: Expr
    cases: tuple[Expr, ...]

    def __str__(self) -> str:
        cases_str = ", ".join(f"branch ↦ {c}" for c in self.cases)
        return (
            f"match ({self.inductive_name}) {self.discriminee} "
            f"motive {self.motive} with [ {cases_str} ]"
        )


@dataclass(frozen=True)
class EMetaVar(Expr):
    """Meta-variable, e.g. ?m."""

    goal_id: str

    def __str__(self) -> str:
        return f"?{self.goal_id}"
