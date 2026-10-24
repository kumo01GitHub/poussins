"""Quotient type framework wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ..ast import EConst, EPi, EVar, Expr, UnivLevelParam, app
from ..environment.library import QuotDeclaration
from .definition import Definition
from .inductive import Inductive


@dataclass(frozen=True, init=False)
class Quot:
    """Quotient type framework wrapper.

    Allows clean DSL syntax based on explicit AST expressions:
        q = Quot[rel](a)
        Quot[rel].sound(a, b, h)
        Quot[rel].lift(type_b, f, compat, q)
        Quot[rel].ind(motive, h, q)
    """

    value: Expr

    def __init__(self, a: Quot | Inductive | Expr) -> None:
        """Construct (Quot.mk .{u} A rel a) upon instantiation."""
        raise NotImplementedError

    @classmethod
    def levels(cls) -> tuple[UnivLevelParam, ...]:
        """Return the universe levels of this quotient type."""
        return tuple(
            UnivLevelParam(param) for param
            in QuotDeclaration.QUOT_DECLARATION.declaration.level_params
        )

    @classmethod
    def type_expr(cls) -> Expr:
        """Return the type expression of the quotient type."""
        return EConst(
            name=QuotDeclaration.QUOT_DECLARATION.declaration.name,
            levels=cls.levels()
        )

    @property
    def type(self) -> Expr:
        """Return the type expression of the quotient type."""
        return self.type_expr()

    @classmethod
    def rel(cls) -> Expr:
        """Return the equivalence relation associated with this quotient type."""
        raise NotImplementedError

    @classmethod
    def mk(cls, a: Quot | Inductive | Expr) -> Quot:
        """Construct (Quot.mk .{u} A rel a)."""
        raise NotImplementedError

    @classmethod
    def sound(
        cls,
        a: Quot | Inductive | Expr,
        b: Quot | Inductive | Expr,
        h: Expr | str | None = None,
    ) -> Expr:
        """Construct (Quot.sound .{u} A r a b h)."""
        raise NotImplementedError

    @classmethod
    def lift(
        cls,
        type_b: Expr,
        f: Definition | Expr,
        compat: Expr,
        q: Quot | Inductive | Expr,
    ) -> Expr:
        """Construct (Quot.lift .{u, v} A r B f compat q)."""
        raise NotImplementedError

    @classmethod
    def ind(
        cls,
        motive: Expr,
        h: Expr,
        q: Quot | Inductive | Expr,
    ) -> Expr:
        """Construct (Quot.ind .{u} A r motive h q)."""
        raise NotImplementedError

    @staticmethod
    def _to_expr(obj: Quot | Inductive | Expr) -> Expr:
        """Extract underlying Expr from Quot instance, Inductive, or Expr."""
        if isinstance(obj, Quot):
            return obj.value
        return Inductive.to_expr(obj)

    @staticmethod
    def _extract_type_a(relation: Definition | Expr) -> Expr:
        """Extract the base type A from the equivalence relation's type definition.

        Strictly throws TypeError if type cannot be extracted (no fallback).
        """
        if isinstance(relation, Definition):
            t = relation.type
            if isinstance(t, EPi):
                return t.domain
            raise TypeError(f"Definition type must be a Pi type (EPi), got {type(t)}")
        raise TypeError(
            f"Expected Definition to extract type A, got raw Expr {type(relation)}"
        )

    def __class_getitem__(cls, relation: Definition | Expr):
        """Return a Quot class bound to the given equivalence relation."""
        rel_expr = Definition.to_expr(relation)
        type_a = Quot._extract_type_a(relation)

        @dataclass(frozen=True, init=False)
        class BoundQuot(Quot):
            REL: ClassVar[Expr] = rel_expr
            TYPE_A: ClassVar[Expr] = type_a

            def __init__(self, a: Quot | Inductive | Expr) -> None:
                """Construct (Quot.mk .{u} A rel a) upon instantiation."""
                decl = QuotDeclaration.QUOT_MK_DECLARATION.declaration
                expr = app(
                    EConst(
                        name=decl.name,
                        levels=tuple(
                            UnivLevelParam(param) for param
                            in decl.level_params
                        )
                    ),
                    BoundQuot.TYPE_A,
                    rel_expr,
                    self._to_expr(a),
                )
                object.__setattr__(self, "value", expr)

            @override
            @classmethod
            def type_expr(cls) -> Expr:
                """Return the type expression of the quotient type."""
                decl = QuotDeclaration.QUOT_DECLARATION.declaration
                return app(
                    EConst(
                        name=decl.name,
                        levels=tuple(
                            UnivLevelParam(param) for param
                            in decl.level_params
                        )
                    ),
                    BoundQuot.TYPE_A,
                    rel_expr,
                )

            @override
            @classmethod
            def rel(cls) -> Expr:
                return cls.REL

            @classmethod
            @override
            def mk(cls, a: Quot | Inductive | Expr) -> BoundQuot:
                """Construct (Quot.mk .{u} A rel a) and wrap it in BoundQuot."""
                return cls(a)

            @classmethod
            @override
            def sound(
                cls,
                a: Quot | Inductive | Expr,
                b: Quot | Inductive | Expr,
                h: Expr | str | None = None,
            ) -> Expr:
                """Construct (Quot.sound .{u} A r a b h)."""
                decl = QuotDeclaration.QUOT_SOUND_DECLARATION.declaration
                if h is None:
                    return app(
                        EConst(
                            name=decl.name,
                            levels=tuple(
                                UnivLevelParam(param) for param
                                in decl.level_params
                            )
                        ),
                        type_a,
                        rel_expr,
                        cls._to_expr(a),
                        cls._to_expr(b),
                    )
                else:
                    return app(
                        EConst(
                            name=decl.name,
                            levels=tuple(
                                UnivLevelParam(param) for param
                                in decl.level_params
                            )
                        ),
                        type_a,
                        rel_expr,
                        cls._to_expr(a),
                        cls._to_expr(b),
                        h if isinstance(h, Expr) else EVar(h)
                    )

            @classmethod
            @override
            def lift(
                cls,
                type_b: Expr,
                f: Definition | Expr,
                compat: Expr,
                q: Quot | Inductive | Expr,
            ) -> Expr:
                """Construct (Quot.lift .{u, v} A r B f compat q)."""
                decl = QuotDeclaration.QUOT_LIFT_DECLARATION.declaration
                f_expr = Definition.to_expr(f)
                return app(
                    EConst(
                        name=decl.name,
                        levels=tuple(
                            UnivLevelParam(param) for param
                            in decl.level_params
                        )
                    ),
                    type_a,
                    rel_expr,
                    type_b,
                    f_expr,
                    compat,
                    cls._to_expr(q),
                )

            @classmethod
            @override
            def ind(
                cls,
                motive: Expr,
                h: Expr,
                q: Quot | Inductive | Expr,
            ) -> Expr:
                """Construct (Quot.ind .{u} A r motive h q)."""
                decl = QuotDeclaration.QUOT_IND_DECLARATION.declaration
                return app(
                    EConst(
                        name=decl.name,
                        levels=tuple(
                            UnivLevelParam(param) for param
                            in decl.level_params
                        )
                    ),
                    type_a,
                    rel_expr,
                    motive,
                    h,
                    cls._to_expr(q),
                )

        return BoundQuot
