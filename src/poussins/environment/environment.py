"""Environment storage and predefined logical declarations."""
from __future__ import annotations

from typing import cast

from ..ast import (
    EApp,
    EConst,
    EPi,
    ESort,
    EVar,
    Expr,
    ExprSerializer,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)
from ..kernel import infer_type
from ..utils.serializer import JsonValue
from .declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)
from .library import (
    BoolDeclaration,
    EmptyDeclaration,
    EqualityDeclaration,
    FinDeclaration,
    ListDeclaration,
    LogicDeclaration,
    NatDeclaration,
    OptionDeclaration,
    ProdDeclaration,
    QuotLibraryDeclaration,
    SigmaDeclaration,
    SumDeclaration,
    UnitDeclaration,
    VectorDeclaration,
)
from .serializer import DeclarationSerializer


class Environment:
    """Collection of named declarations."""

    def __init__(self):
        """Initialize an empty environment."""
        self.declarations: dict[str, Declaration] = {}

    def add(self, declaration: Declaration):
        """Add a declaration to the environment."""
        if declaration.name in self.declarations:
            raise ValueError(
                f"Declaration with name '{declaration.name}' already exists."
            )
        self.declarations[declaration.name] = declaration

    def get(self, name: str) -> Declaration | None:
        """Return the declaration with the given name, if it exists."""
        return self.declarations.get(name)

    def has(self, name: str) -> bool:
        """Check if a declaration with the given name exists in the environment."""
        return name in self.declarations

    def update(self, other: Environment):
        """Merge declarations from another environment into this one."""
        self.declarations.update(other.declarations)

    def items(self):
        """Return the environment declarations as `(name, declaration)` pairs."""
        return self.declarations.items()

    def to_context(self) -> dict[str, Expr]:
        """Convert the environment to a context dictionary mapping names to types."""
        return {name: decl.type for name, decl in self.declarations.items()}

    def declare(self, data: dict[str, JsonValue] | Declaration) -> Declaration:
        """Declare a new declaration in the environment."""
        if isinstance(data, Declaration):
            self.add(data)
            return data
        else:
            decl = DeclarationSerializer.from_dict(data)
            self.add(decl)
            return decl

    def declare_inductive(  # noqa: PLR0913
        self,
        name: str,
        constructors: list[dict[str, JsonValue | Expr]],
        *,
        level_params: tuple[str, ...] = (),
        type: Expr | dict[str, JsonValue] | None = None,
        num_params: int | None = None,
        num_indices: int | None = None,
        recursor_type: Expr | dict[str, JsonValue] | None = None,
    ) -> tuple[InductiveDeclaration, list[ConstructorDeclaration], RecursorDeclaration]:
        """Declare an inductive type along with its constructors and recursor.

        Example:
            ```python
            # Initialize an environment
            env = Environment()

            # Declare the natural numbers inductive type
            ind_decl, ctor_decls, rec_decl = env.declare_inductive(
                name="Nat",
                constructors=[
                    {
                        "name": "zero",
                        "type": EConst(name="Nat", levels=()),
                    },
                    {
                        "name": "succ",
                        "type": EPi(
                            var="n",
                            domain=EConst(name="Nat", levels=()),
                            body=EConst(name="Nat", levels=()),
                        ),
                    },
                ],
            )
            ```

        """
        # 1. Automatically qualify short names (e.g., "zero" -> "Nat.zero")
        full_constructors: list[tuple[str, dict[str, JsonValue | Expr]]] = [
            (f"{name}.{c['name']}", c) for c in constructors
        ]
        ctor_full_names: tuple[str, ...] = tuple(
            full_name for full_name, _ in full_constructors
        )

        # 2. Automatically build type, num_params, and num_indices if not specified
        if type is None or num_params is None or num_indices is None:
            built_type, b_p, b_i = self._build_inductive_type_and_counts(
                name, constructors, level_params
            )
            type = type if type is not None else built_type
            num_params = num_params if num_params is not None else b_p
            num_indices = num_indices if num_indices is not None else b_i

        # 3. Automatically build recursor type if not specified
        if recursor_type is None:
            recursor_type = self._build_recursor_type(
                name, type, constructors, level_params, num_params, num_indices
            )

        # 4. Convert to AST representation and perform preliminary type checking
        ind_type_expr = (
            ExprSerializer.from_dict(type) if isinstance(type, dict) else type
        )
        rec_type_expr = (
            ExprSerializer.from_dict(recursor_type)
            if isinstance(recursor_type, dict)
            else recursor_type
        )

        # (a) Check that the inductive type is a Sort
        ind_sort = infer_type(ind_type_expr, context={}, metavars={}, env=self)
        if not isinstance(ind_sort, ESort):
            raise ValueError(
                f"Inductive type '{name}' must be a Sort, but got: {ind_sort}"
            )

        # 5. Instantiate Declarations
        ind_decl = InductiveDeclaration(
            name=name,
            level_params=level_params,
            type=ind_type_expr,
            constructor_names=ctor_full_names,
        )

        ctor_decls: list[ConstructorDeclaration] = []
        for full_name, ctor in full_constructors:
            ctor_expr = cast(
                Expr,
                (
                    ExprSerializer.from_dict(ctor["type"])
                    if isinstance(ctor["type"], dict)
                    else ctor["type"]
                )
            )
            # (b) Check that each constructor type is well-typed
            _ = infer_type(ctor_expr, context={}, metavars={}, env=self)

            ctor_decls.append(
                ConstructorDeclaration(
                    name=full_name,
                    level_params=level_params,
                    type=ctor_expr,
                    inductive_name=name,
                )
            )

        # (c) Check that the recursor type is well-typed
        _ = infer_type(rec_type_expr, context={}, metavars={}, env=self)
        rec_decl = RecursorDeclaration(
            name=f"{name}.rec",
            level_params=level_params,
            type=rec_type_expr,
            inductive_name=name,
            num_params=num_params,
            num_indices=num_indices,
            num_minors=len(constructors),
        )

        # 6. Add all created declarations to the environment
        self.add(ind_decl)
        for c_decl in ctor_decls:
            self.add(c_decl)
        self.add(rec_decl)

        return ind_decl, ctor_decls, rec_decl

    def _build_inductive_type_and_counts(
        self,
        name: str,
        constructors: list[dict[str, JsonValue | Expr]],
        level_params: tuple[str, ...],
    ) -> tuple[Expr, int, int]:
        """Construct the inductive type and count parameters and indices."""
        univ = (
            UnivLevelParam(level_params[0])
            if level_params
            else UnivLevelSucc(UnivLevelZero())
        )
        base_type: Expr = ESort(level=univ)
        num_params = 0
        num_indices = 0

        if constructors:
            raw_ctor_type = constructors[0]["type"]
            first_ctor_type = (
                ExprSerializer.from_dict(raw_ctor_type)
                if isinstance(raw_ctor_type, dict)
                else raw_ctor_type
            )
            curr = first_ctor_type
            while isinstance(curr, EPi):
                if isinstance(curr.body, EPi):
                    num_params += 1
                    curr = curr.body
                else:
                    break

        return base_type, num_params, num_indices

    def _build_recursor_type(  # noqa: PLR0913
        self,
        name: str,
        ind_type: Expr | dict[str, JsonValue],
        constructors: list[dict[str, JsonValue | Expr]],
        level_params: tuple[str, ...],
        num_params: int,
        num_indices: int,
    ) -> Expr:
        """Construct the recursor type for the inductive type."""
        motive_level = (
            UnivLevelParam("v")
            if level_params
            else UnivLevelSucc(UnivLevelZero())
        )
        univ_levels = tuple(UnivLevelParam(p) for p in level_params)
        target_const: Expr = EConst(name=name, levels=univ_levels)

        ind_type_expr = (
            ExprSerializer.from_dict(ind_type)
            if isinstance(ind_type, dict)
            else ind_type
        )

        # 1. Extract parameter and index domains from the inductive type
        param_domains: list[Expr] = []
        index_domains: list[Expr] = []
        curr = ind_type_expr

        for _ in range(num_params):
            if isinstance(curr, EPi):
                param_domains.append(curr.domain)
                curr = curr.body

        for _ in range(num_indices):
            if isinstance(curr, EPi):
                index_domains.append(curr.domain)
                curr = curr.body

        param_args = [EVar(f"p{i}") for i in range(num_params)]
        index_args = [EVar(f"idx{i}") for i in range(num_indices)]

        applied_target = target_const
        for p_arg in param_args:
            applied_target = EApp(fn=applied_target, arg=p_arg)
        for i_arg in index_args:
            applied_target = EApp(fn=applied_target, arg=i_arg)

        # 2. Construct the motive type:
        #    Π (idx0 : I0) ... (t : Target p ... idx ...), Sort v
        motive_target = EPi(
            var="t",
            domain=applied_target,
            body=ESort(level=motive_level),
        )
        motive_type = motive_target
        for i, idx_dom in reversed(list(enumerate(index_domains))):
            motive_type = EPi(var=f"idx{i}", domain=idx_dom, body=motive_type)

        # 3. Construct the minor premise types for each constructor
        rec_type: Expr = ESort(level=motive_level)

        for ctor in reversed(constructors):
            raw_ctor_type = ctor["type"]
            ctor_type = (
                ExprSerializer.from_dict(raw_ctor_type)
                if isinstance(raw_ctor_type, dict)
                else raw_ctor_type
            )
            ctor_name_str = cast(str, ctor["name"])
            ctor_const = EConst(name=f"{name}.{ctor_name_str}", levels=univ_levels)

            if isinstance(ctor_type, EPi):
                minor_domain = EPi(
                    var="n",
                    domain=ctor_type.domain,
                    body=EApp(fn=EVar("P"), arg=EVar("n")),
                )
                minor_body = EApp(fn=EVar("P"), arg=EApp(fn=ctor_const, arg=EVar("n")))
                minor_type = EPi(var="ih", domain=minor_domain, body=minor_body)
            else:
                minor_type = EApp(fn=EVar("P"), arg=ctor_const)

            rec_type = EPi(var=f"m_{ctor_name_str}", domain=minor_type, body=rec_type)

        # 4. Major Premise (the target of the recursor):
        #    Π (idx0 : I0) ... (t : Target p ... idx ...), P idx ... t
        motive_app: Expr = EVar("P")
        for i_arg in index_args:
            motive_app = EApp(fn=motive_app, arg=i_arg)
        motive_app = EApp(fn=motive_app, arg=EVar("t"))

        major_target = EPi(var="t", domain=applied_target, body=motive_app)
        for i, idx_dom in reversed(list(enumerate(index_domains))):
            major_target = EPi(var=f"idx{i}", domain=idx_dom, body=major_target)

        # 5. Construct the full recursor type (Motive -> Minors -> Major)
        full_rec_type = EPi(
            var="P",
            domain=motive_type,
            body=EPi(var="minor", domain=rec_type, body=major_target),
        )

        # 6. Wrap the full recursor type with parameter abstractions
        for i, p_dom in reversed(list(enumerate(param_domains))):
            full_rec_type = EPi(var=f"p{i}", domain=p_dom, body=full_rec_type)

        return full_rec_type

    @classmethod
    def standard(cls) -> Environment:
        """Create a standard environment."""
        env = cls()

        # ------------------------------------------------------------------
        # Logical Declarations
        # ------------------------------------------------------------------
        for item in LogicDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Equality Declarations
        # ------------------------------------------------------------------
        for item in EqualityDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Boolean Declarations
        # ------------------------------------------------------------------
        for item in BoolDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Natural Number Declarations
        # ------------------------------------------------------------------
        for item in NatDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Product Declarations
        # ------------------------------------------------------------------
        for item in ProdDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Sigma Declarations
        # ------------------------------------------------------------------
        for item in SigmaDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Option Declarations
        # ------------------------------------------------------------------
        for item in OptionDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # List Declarations
        # ------------------------------------------------------------------
        for item in ListDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Unit Declarations
        # ------------------------------------------------------------------
        for item in UnitDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Sum Declarations
        # ------------------------------------------------------------------
        for item in SumDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Empty Declarations
        # ------------------------------------------------------------------
        for item in EmptyDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Finite Declarations
        # ------------------------------------------------------------------
        for item in FinDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Vector Declarations
        # ------------------------------------------------------------------
        for item in VectorDeclaration:
            env.add(item.declaration)

        # ------------------------------------------------------------------
        # Quotient Declarations
        # ------------------------------------------------------------------
        for item in QuotLibraryDeclaration:
            env.add(item.declaration)

        return env
