"""Quotient type framework wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ..ast import EPi, EVar, Expr, app
from ..environment import Environment, QuotientDeclaration, const
from ..environment.library import (
    EQ_IND_SPEC,
    QUOT_DECLARATION,
    QUOT_IND_DECLARATION,
    QUOT_LIFT_DECLARATION,
    QUOT_MK_DECLARATION,
    QUOT_SOUND_DECLARATION,
)
from .declaration import declare_quot
from .definition import Definition
from .environment import STANDARD_ENV
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

    env: ClassVar[Environment | None] = None
    value: Expr

    def __init__(self, a: Quot | Inductive | Expr) -> None:
        """Construct (Quot.mk .{u} A rel a) upon instantiation."""
        raise NotImplementedError

    @classmethod
    def type_ref(cls) -> Expr:
        """Return the type expression of the quotient type."""
        return const(STANDARD_ENV, QUOT_DECLARATION.name)

    @property
    def type(self) -> Expr:
        """Return the type expression of the quotient type."""
        return self.type_ref()

    @classmethod
    def declare(cls, env: Environment) -> QuotientDeclaration:
        """Declare the quotient type in the environment."""
        declaration = declare_quot(env)
        cls.env = env
        return declaration

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

    @classmethod
    def eq(
        cls,
        left: Quot | Expr,
        right: Quot | Expr,
    ) -> Expr:
        """Construct (Quot.eq .{u} A r left right)."""
        raise NotImplementedError

    @classmethod
    def to_expr(cls, obj: Quot | Expr) -> Expr:
        """Return the underlying expression of a Quot instance or raw Expr."""
        return obj.value if isinstance(obj, Quot) else obj

    @staticmethod
    def _to_expr(obj: Quot | Inductive | Expr) -> Expr:
        """Extract underlying Expr from Quot instance, Inductive, or Expr."""
        if isinstance(obj, (Quot, Inductive)):
            return obj.value
        else:
            return obj

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
                expr = app(
                    const(STANDARD_ENV, QUOT_MK_DECLARATION.name),
                    BoundQuot.TYPE_A,
                    rel_expr,
                    self._to_expr(a),
                )
                object.__setattr__(self, "value", expr)

            @override
            @classmethod
            def type_ref(cls) -> Expr:
                """Return the type expression of the quotient type."""
                return app(
                    const(STANDARD_ENV, QUOT_DECLARATION.name),
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
                decl = QUOT_SOUND_DECLARATION
                if h is None:
                    return app(
                        const(STANDARD_ENV, decl.name),
                        type_a,
                        rel_expr,
                        cls._to_expr(a),
                        cls._to_expr(b),
                    )
                else:
                    return app(
                        const(STANDARD_ENV, decl.name),
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
                decl = QUOT_LIFT_DECLARATION
                f_expr = Definition.to_expr(f)
                return app(
                    const(STANDARD_ENV, decl.name),
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
                decl = QUOT_IND_DECLARATION
                return app(
                    const(STANDARD_ENV, decl.name),
                    type_a,
                    rel_expr,
                    motive,
                    h,
                    cls._to_expr(q),
                )

            @classmethod
            @override
            def eq(
                cls,
                left: Quot | Expr,
                right: Quot | Expr,
            ) -> Expr:
                """Construct (Quot.eq .{u} A r left right)."""
                return app(
                    const(
                        cls.env if cls.env is not None else STANDARD_ENV,
                        EQ_IND_SPEC.name
                    ),
                    cls.type_ref(),
                    cls.to_expr(left),
                    cls.to_expr(right),
                )

        return BoundQuot
