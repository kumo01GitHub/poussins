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
    build_pi_chain,
    flatten_app_chain,
)
from ..kernel import check_type, infer_type
from ..utils.serializer import JsonValue
from .declaration import (
    AxiomDeclaration,
    ConstructorDeclaration,
    Declaration,
    DefinitionDeclaration,
    InductiveDeclaration,
    RecursorDeclaration,
    TheoremDeclaration,
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

    def declare_inductive(
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
            built_type, b_p, b_i = self._build_inductive_type(
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

    def declare_axiom(
        self,
        name: str,
        type: Expr | dict[str, JsonValue],
        *,
        level_params: tuple[str, ...] = (),
    ) -> AxiomDeclaration:
        """Declare a new axiom in the environment after type checking.

        Example:
            ```python
            # Declare an axiom: p_axiom : Prop
            axiom_decl = env.declare_axiom(
                name="p_axiom",
                type=ESort(UnivLevelZero()),
            )
            ```

        """
        # 1. Convert dict representation to AST if necessary
        type_expr = ExprSerializer.from_dict(type) if isinstance(type, dict) else type

        # 2. Kernel check: verify that the axiom's type itself is well-typed
        type_sort = infer_type(type_expr, context={}, metavars={}, env=self)
        if not isinstance(type_sort, ESort):
            raise ValueError(
                f"Axiom '{name}' type must be a Sort, but got: {type_sort}"
            )

        # 3. Instantiate and register the declaration
        axiom_decl = AxiomDeclaration(
            name=name,
            level_params=level_params,
            type=type_expr,
        )
        self.add(axiom_decl)

        return axiom_decl

    def declare_theorem(
        self,
        name: str,
        type: Expr | dict[str, JsonValue],
        value: Expr | dict[str, JsonValue],
        *,
        level_params: tuple[str, ...] = (),
    ) -> TheoremDeclaration:
        """Declare a theorem after type checking both type and value proof.

        Example:
            ```python
            # Declare a theorem: id_proof : A -> A
            theorem_decl = env.declare_theorem(
                name="id_proof",
                type=EPi("x", EVar("A"), EVar("A")),
                value=ELam("x", EVar("A"), EVar("x")),
            )
            ```

        """
        # 1. Convert dict representations to AST if necessary
        type_expr = (
            ExprSerializer.from_dict(type)
            if isinstance(type, dict) else type
        )
        value_expr = (
            ExprSerializer.from_dict(value)
            if isinstance(value, dict) else value
        )

        # 2. Kernel check: verify that the type statement is well-typed
        type_sort = infer_type(type_expr, context={}, metavars={}, env=self)
        if not isinstance(type_sort, ESort):
            raise ValueError(
                f"Theorem '{name}' type statement must be a Sort, but got: {type_sort}"
            )

        # 3. Kernel check: verify that the proof value matches the declared theorem type
        if not check_type(value_expr, type_expr, context={}, metavars={}, env=self):
            inferred_val_type = infer_type(
                value_expr,
                context={},
                metavars={},
                env=self
            )
            raise ValueError(
                f"Type mismatch for theorem '{name}'. "
                + f"Declared type: {type_expr}, "
                + f"but proof value has type: {inferred_val_type}"
            )

        # 4. Instantiate and register the declaration
        theorem_decl = TheoremDeclaration(
            name=name,
            level_params=level_params,
            type=type_expr,
            value=value_expr,
        )
        self.add(theorem_decl)

        return theorem_decl

    def declare_definition(
        self,
        name: str,
        value: Expr | dict[str, JsonValue],
        type: Expr | dict[str, JsonValue] | None = None,
        *,
        level_params: tuple[str, ...] = (),
    ) -> DefinitionDeclaration:
        """Declare a new definition in the environment.

        If `type` is omitted, its type is automatically inferred.

        Example:
            ```python
            # Declare a definition: my_id := λ x : A, x
            def_decl = env.declare_definition(
                name="my_id",
                value=ELam("x", EVar("A"), EVar("x")),
            )
            ```

        """
        # 1. Convert dict representations to AST if necessary
        value_expr = (
            ExprSerializer.from_dict(value)
            if isinstance(value, dict) else value
        )
        type_expr = (
            ExprSerializer.from_dict(type)
            if isinstance(type, dict) else type
        )

        # 2. If type is not explicitly provided, infer it automatically from value
        if type_expr is None:
            type_expr = infer_type(value_expr, context={}, metavars={}, env=self)
        else:
            # Check that explicit type is a valid Sort
            type_sort = infer_type(type_expr, context={}, metavars={}, env=self)
            if not isinstance(type_sort, ESort):
                raise ValueError(
                    f"Definition '{name}' type must be a Sort, but got: {type_sort}"
                )

            # Kernel check: verify that value matches the specified type
            if not check_type(value_expr, type_expr, context={}, metavars={}, env=self):
                inferred_val_type = infer_type(
                    value_expr, context={}, metavars={}, env=self
                )
                raise ValueError(
                    f"Type mismatch for definition '{name}'. "
                    + f"Specified type: {type_expr}, "
                    + f"but value has type: {inferred_val_type}"
                )

        # 3. Instantiate and register the declaration
        def_decl = DefinitionDeclaration(
            name=name,
            level_params=level_params,
            type=type_expr,
            value=value_expr,
        )
        self.add(def_decl)

        return def_decl

    def declare_quot(
        self,
    ) -> tuple[
        AxiomDeclaration, AxiomDeclaration, AxiomDeclaration, AxiomDeclaration
    ]:
        """Declare Quotient primitives (Quot, Quot.mk, Quot.lift, Quot.ind).

        Example:
            ```python
            env = Environment()
            quot_decl, mk_decl, lift_decl, ind_decl = env.declare_quot()
            ```

        """
        u, v = UnivLevelParam("u"), UnivLevelParam("v")
        sort_u, sort_v, prop = ESort(u), ESort(v), ESort(UnivLevelZero())
        alpha, r_var, beta_var = EVar("α"), EVar("r"), EVar("β")

        # Common relation type: r : α -> α -> Prop
        rel_type = build_pi_chain([("_", alpha), ("_", alpha)], prop)
        quot_app = EApp(EApp(EConst("Quot", (u,)), alpha), r_var)

        # 1. Quot : Π (α : Sort u) (r : α -> α -> Prop), Sort u
        quot_decl = AxiomDeclaration(
            name="Quot",
            level_params=("u",),
            type=build_pi_chain([("α", sort_u), ("r", rel_type)], sort_u),
        )

        # 2. Quot.mk : Π (α : Sort u) (r : α -> α -> Prop) (a : α), Quot α r
        quot_mk_decl = AxiomDeclaration(
            name="Quot.mk",
            level_params=("u",),
            type=build_pi_chain(
                [("α", sort_u), ("r", rel_type), ("a", alpha)],
                quot_app
            ),
        )

        # 3. Quot.lift : Π (α : Sort u) (r : α -> α -> Prop) (β : Sort v)
        #                (f : α -> β) (h : proof) (q : Quot α r), β
        f_type = EPi("a", alpha, beta_var)
        quot_lift_decl = AxiomDeclaration(
            name="Quot.lift",
            level_params=("u", "v"),
            type=build_pi_chain(
                [
                    ("α", sort_u),
                    ("r", rel_type),
                    ("β", sort_v),
                    ("f", f_type),
                    ("proof", prop),
                    ("q", quot_app),
                ],
                beta_var,
            ),
        )

        # 4. Quot.ind : Π (α : Sort u) (r : α -> α -> Prop) (β : Quot α r -> Prop)
        #               (h : Π a : α, β (Quot.mk r a)) (q : Quot α r), β q
        beta_motive = EPi("q", quot_app, prop)
        mk_app = EApp(EApp(EConst("Quot.mk", (u,)), alpha), r_var)
        ind_minor = EPi("a", alpha, EApp(beta_var, EApp(mk_app, EVar("a"))))
        ind_major = EApp(beta_var, EVar("q"))

        quot_ind_decl = AxiomDeclaration(
            name="Quot.ind",
            level_params=("u",),
            type=build_pi_chain(
                [
                    ("α", sort_u),
                    ("r", rel_type),
                    ("β", beta_motive),
                    ("h", ind_minor),
                    ("q", quot_app),
                ],
                ind_major,
            ),
        )

        decls = (quot_decl, quot_mk_decl, quot_lift_decl, quot_ind_decl)
        for d in decls:
            self.add(d)

        return decls

    def _build_inductive_type(
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
        base_sort: Expr = ESort(level=univ)

        if not constructors:
            return base_sort, 0, 0

        # Extract parameter and index domain structures from the first constructor
        raw_ctor_type = constructors[0]["type"]
        first_ctor_type = cast(
            Expr,
            ExprSerializer.from_dict(raw_ctor_type)
            if isinstance(raw_ctor_type, dict)
            else raw_ctor_type
        )

        binders: list[tuple[str, Expr]] = []
        curr = first_ctor_type

        # Collect binders leading up to the target inductive type
        while isinstance(curr, EPi):
            binders.append((curr.var, curr.domain))
            curr = curr.body

        # Verify that the constructor target actually constructs `name`
        head, _ = flatten_app_chain(curr)
        if isinstance(head, EConst) and head.name != name:
            raise ValueError(
                f"Constructor target name '{head.name}' "
                + f"does not match inductive type '{name}'"
            )

        num_params = len(binders)
        num_indices = 0

        # Build proper inductive type: Π (p1 : A1) ... (pn : An), Sort u
        ind_type = build_pi_chain(binders, base_sort)

        return ind_type, num_params, num_indices

    def _build_recursor_type(
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
