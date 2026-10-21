"""Quotient type framework wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ..ast import EConst, Expr, UnivLevelParam, build_app_chain
from ..environment.library import QuotDeclaration
from .definition import Definition
from .inductive import Inductive


@dataclass(frozen=True, init=False)
class Quot:
    """Quotient type framework wrapper.

    Allows clean DSL syntax based on explicit AST expressions:
        Quot[rel](a)
        Quot[rel].sound(h)
        Quot[rel].lift(f, h, q)
        Quot[rel].ind(motive, h, q)
    """

    def __class_getitem__(cls, rel: Definition | Expr):
        """Return a Quot class bound to the given equivalence relation."""
        @dataclass(frozen=True, init=False)
        class BoundQuot:
            REL: ClassVar[Expr] = Definition.to_expr(rel)

            @classmethod
            def mk(cls, a: Inductive | Expr) -> Expr:
                """Construct (Quot.mk .{u} rel a)."""
                decl = QuotDeclaration.QUOT_MK_DECLARATION.declaration
                return build_app_chain(
                    EConst(
                        name=decl.name,
                        levels=tuple(
                            UnivLevelParam(param) for param
                            in decl.level_params
                        )
                    ),
                    cls.REL,
                    Inductive.to_expr(a),
                )

            @classmethod
            def __call__(cls, a: Inductive | Expr) -> Expr:
                """Syntactic sugar: Quot[rel](a) is equivalent to Quot.mk rel a."""
                return cls.mk(a)

            @classmethod
            def sound(cls, h: Expr) -> Expr:
                """Construct (Quot.sound .{u} rel h)."""
                decl = QuotDeclaration.QUOT_SOUND_DECLARATION.declaration
                return build_app_chain(
                    EConst(
                        name=decl.name,
                        levels=tuple(
                            UnivLevelParam(param) for param
                            in decl.level_params
                        )
                    ),
                    cls.REL,
                    h,
                )

            @classmethod
            def lift(cls, f: Expr, compat: Expr, q: Expr) -> Expr:
                """Construct (Quot.lift .{u, v} rel f compat q)."""
                decl = QuotDeclaration.QUOT_LIFT_DECLARATION.declaration
                return build_app_chain(
                    EConst(
                        name=decl.name,
                        levels=tuple(
                            UnivLevelParam(param) for param
                            in decl.level_params
                        )
                    ),
                    cls.REL,
                    f,
                    compat,
                    q,
                )

            @classmethod
            def ind(cls, motive: Expr, h: Expr, q: Expr) -> Expr:
                """Construct (Quot.ind .{u} rel motive h q)."""
                decl = QuotDeclaration.QUOT_IND_DECLARATION.declaration
                return build_app_chain(
                    EConst(
                        name=decl.name,
                        levels=tuple(
                            UnivLevelParam(param) for param
                            in decl.level_params
                        )
                    ),
                    cls.REL,
                    motive,
                    h,
                    q,
                )

        return BoundQuot
