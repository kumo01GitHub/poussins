"""
Environment: a collection of declarations (axioms, theorems, etc.) with unique names.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Final, Optional

from ..ast import (
    Expr,
    ETop,
    ProofTerm,
    PTrueI,
    Sort,
    FunctionSymbol,
)
from ..errors import FrameworkError
from ..kernel import ProofAssurance, Context


class DeclarationKind(str, Enum):
    THEOREM = "theorem"
    AXIOM = "axiom"
    SORT = "sort"
    FUNCTION_SYMBOL = "function_symbol"


@dataclass(frozen=True)
class Declaration:
    name: str
    kind: DeclarationKind
    statement: Optional[Expr] = None
    assignment: Optional[ProofTerm] = None
    assurance: ProofAssurance = ProofAssurance.UNKNOWN
    sort: Optional[Sort] = None
    function_symbol: Optional[FunctionSymbol] = None

    @classmethod
    def theorem(
        cls,
        name: str,
        statement: Expr,
        assignment: Optional[ProofTerm],
        assurance: ProofAssurance,
    ) -> Declaration:
        return cls(
            name=name,
            kind=DeclarationKind.THEOREM,
            statement=statement,
            assignment=assignment,
            assurance=assurance,
        )

    @classmethod
    def axiom(cls, name: str, statement: Expr) -> Declaration:
        return cls(
            name=name,
            kind=DeclarationKind.AXIOM,
            statement=statement,
            assignment=None,
            assurance=ProofAssurance.TRUSTED,
        )

    @classmethod
    def sort_decl(cls, name: str, sort: Sort) -> Declaration:
        return cls(name=name, kind=DeclarationKind.SORT, sort=sort)

    @classmethod
    def function_decl(cls, symbol: FunctionSymbol) -> Declaration:
        return cls(
            name=symbol.name,
            kind=DeclarationKind.FUNCTION_SYMBOL,
            function_symbol=symbol,
        )

    @property
    def has_statement(self) -> bool:
        return self.statement is not None


DECLARATION_TOP: Final[Declaration] = Declaration(
    name="TOP",
    kind=DeclarationKind.THEOREM,
    statement=ETop(),
    assignment=PTrueI(),
    assurance=ProofAssurance.VERIFIED,
)


@dataclass
class Environment:
    declarations: dict[str, Declaration] = field(default_factory=dict)

    @classmethod
    def with_nat_prelude(cls) -> Environment:
        env = cls()
        nat = "Nat"
        env.add(("Nat", nat))
        env.add(FunctionSymbol("zero", (), nat))
        env.add(FunctionSymbol("succ", (nat,), nat))
        env.add(FunctionSymbol("add", (nat, nat), nat))
        env.add(FunctionSymbol("mul", (nat, nat), nat))
        env.add(FunctionSymbol("lt", (nat, nat), "Prop"))
        env.add(FunctionSymbol("le", (nat, nat), "Prop"))
        return env

    def add_declaration(self, declaration: Declaration, name: Optional[str] = None):
        if declaration.name == DECLARATION_TOP.name:
            raise FrameworkError("Cannot add a declaration with the reserved name 'TOP'.")
        key = name if name is not None else declaration.name
        self.declarations[key] = declaration

    def add(
        self,
        entry: Declaration | FunctionSymbol | tuple[str, Sort],
        name: Optional[str] = None,
    ):
        """Add an environment entry.

        Supported entries:
        - Declaration
        - FunctionSymbol
        - (name, Sort)
        """
        if isinstance(entry, Declaration):
            self.add_declaration(entry, name=name)
            return
        if isinstance(entry, FunctionSymbol):
            self.add_declaration(Declaration.function_decl(entry), name=name)
            return
        if isinstance(entry, tuple) and len(entry) == 2 and isinstance(entry[1], Sort):
            sort_name, sort = entry
            self.add_declaration(Declaration.sort_decl(sort_name, sort), name=name)
            return

        raise FrameworkError("Unsupported entry type for Environment.add.")

    def get(self, name: str) -> Optional[Declaration]:
        if name == DECLARATION_TOP.name:
            return DECLARATION_TOP
        return self.declarations.get(name)

    def add_sort(self, name: str, sort: Sort):
        self.add_declaration(Declaration.sort_decl(name, sort))

    def add_function(self, symbol: FunctionSymbol):
        self.add_declaration(Declaration.function_decl(symbol))

    def extend_context(self, context: Context) -> Context:
        sorts: dict[str, Sort] = {}
        fn_symbols: dict[str, FunctionSymbol] = {}

        for declaration in self.declarations.values():
            match declaration.kind:
                case DeclarationKind.SORT:
                    if declaration.sort is not None:
                        sorts[declaration.name] = declaration.sort
                case DeclarationKind.FUNCTION_SYMBOL:
                    if declaration.function_symbol is not None:
                        fn_symbols[declaration.name] = declaration.function_symbol
                case _:
                    pass

        return context.add_sorts(sorts).add_fn_symbols(fn_symbols)

    def update(self, other: Environment):
        self.declarations.update(other.declarations)

    def items(self):
        return self.declarations.items()
