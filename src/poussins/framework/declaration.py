"""Module for declaring axioms, definitions, inductive types, and quotients."""
from __future__ import annotations

from collections.abc import Sequence

from ..ast import (
    EApp,
    EConst,
    ELam,
    EPi,
    ESort,
    EVar,
    Expr,
    UnivLevelParam,
    app,
    decompose_app,
    substitute_var,
)
from ..environment import (
    AxiomDeclaration,
    ConstructorDeclaration,
    DefinitionDeclaration,
    Environment,
    InductiveDeclaration,
    QuotientDeclaration,
    RecursorDeclaration,
    TheoremDeclaration,
)
from ..environment.library import QuotDeclaration
from ..kernel import (
    register_axiom,
    register_definition,
    register_inductive,
    register_quotient,
    register_theorem,
)


def declare_axiom(
    env: Environment,
    name: str,
    statement: Expr,
    level_params: tuple[str, ...] = ()
) -> AxiomDeclaration:
    """Declare a new axiom in the given environment.

    Args:
        env: The environment to which the axiom will be added.
        name: The name of the axiom.
        statement: The type of the axiom.
        level_params: Optional tuple of universe level parameters for the axiom.

    Returns:
        The created AxiomDeclaration instance.

    """
    decl = AxiomDeclaration(
        name=name,
        type=statement,
        level_params=level_params,
    )
    register_axiom(env, decl)

    return decl


def declare_definition(
    env: Environment,
    name: str,
    type: Expr,
    value: Expr,
    level_params: tuple[str, ...] = ()
) -> DefinitionDeclaration:
    """Declare a new definition in the given environment.

    Args:
        env: The environment to which the definition will be added.
        name: The name of the definition.
        type: The type of the definition.
        value: The value of the definition.
        level_params: Optional tuple of universe level parameters for the definition.

    Returns:
        The created DefinitionDeclaration instance.

    """
    decl = DefinitionDeclaration(
        name=name,
        type=type,
        value=value,
        level_params=level_params,
    )
    register_definition(env, decl)

    return decl


def declare_theorem(
    env: Environment,
    name: str,
    statement: Expr,
    term: Expr,
    level_params: tuple[str, ...] = ()
) -> TheoremDeclaration:
    """Declare a new theorem in the given environment.

    Args:
        env: The environment to which the theorem will be added.
        name: The name of the theorem.
        statement: The type of the theorem.
        term: The value of the theorem.
        level_params: Optional tuple of universe level parameters for the theorem.

    Returns:
        The created TheoremDeclaration instance.

    """
    decl = TheoremDeclaration(
        name=name,
        type=statement,
        value=term,
        level_params=level_params,
    )
    register_theorem(env, decl)

    return decl


def declare_inductive(
    env: Environment,
    name: str,
    type: Expr,
    constructors: Sequence[tuple[str, Expr]],
    level_params: tuple[str, ...] = (),
) -> InductiveDeclaration:
    """Declare a new inductive type in the given environment."""
    inductive_decl = InductiveDeclaration(
        name=name,
        level_params=level_params,
        type=type,
        constructor_names=tuple(c_name for c_name, _ in constructors),
        recursor_names=(f"{name}.rec",)
    )

    constructor_decls = [
        ConstructorDeclaration(
            name=c_name,
            level_params=level_params,
            type=c_type,
            inductive_name=name,
        )
        for c_name, c_type in constructors
    ]

    recursor_decl = _build_recursor(inductive_decl, constructor_decls)

    register_inductive(env, inductive_decl, constructor_decls, recursor_decl)

    return inductive_decl

def _build_recursor(
    inductive_decl: InductiveDeclaration,
    constructor_decls: Sequence[ConstructorDeclaration],
) -> RecursorDeclaration:
    """Build the recursor declaration."""
    ind_name = inductive_decl.name
    rec_name = inductive_decl.recursor_names[0]

    # 0. Collect used names to avoid collisions
    used_names: set[str] = set(inductive_decl.level_params)

    # 1. Generate a fresh name for the motive level parameter
    motive_level = _fresh_name("v", used_names)
    level_params = tuple(list(inductive_decl.level_params) + [motive_level])

    # 2. Extract parameters from the inductive type and count total Pis for indices
    num_params = 0
    total_pis = 0
    param_binders: list[tuple[str, Expr]] = []
    curr = inductive_decl.type
    while isinstance(curr, EPi):
        total_pis += 1
        p_name = _fresh_name(curr.var, used_names)
        param_binders.append((p_name, curr.domain))
        curr = curr.body
        num_params += 1

    # Number of indices is total binders in type minus parameters
    num_indices = max(0, total_pis - num_params)

    # 3. Construct the target expression: InductiveType applied to parameters
    ind_levels = tuple(UnivLevelParam(lp) for lp in inductive_decl.level_params)
    target_expr = EConst(ind_name, ind_levels)
    for p_name, _ in param_binders:
        target_expr = EApp(target_expr, EVar(p_name))

    # 4. Construct the motive type: (t : target_expr) -> Sort v
    motive_domain = target_expr
    motive_sort = ESort(UnivLevelParam(motive_level))

    motive_var = _fresh_name("motive", used_names)
    t_var = _fresh_name("t", used_names)

    # Type of motive: (t : target_expr) -> Sort v
    motive_type = EPi(var=t_var, domain=motive_domain, body=motive_sort)

    num_minors = len(constructor_decls)

    # 5. Build minor premises for each constructor
    minor_premises: list[tuple[str, Expr]] = []

    for i, ctor in enumerate(constructor_decls):
        # Extract constructor raw binders (skipping parameters)
        ctor_curr = ctor.type
        for _ in range(num_params):
            if isinstance(ctor_curr, EPi):
                ctor_curr = ctor_curr.body

        raw_binders: list[tuple[str, Expr]] = []
        while isinstance(ctor_curr, EPi):
            raw_binders.append((ctor_curr.var, ctor_curr.domain))
            ctor_curr = ctor_curr.body

        # Map constructor's parameter names to the current parameterized binders
        curr_t = ctor.type
        ctor_param_names = []
        for _ in range(num_params):
            if isinstance(curr_t, EPi):
                ctor_param_names.append(curr_t.var)
                curr_t = curr_t.body

        param_subst: dict[str, Expr] = {
            c_p_name: EVar(p_name)
            for c_p_name, (p_name, _)
            in zip(ctor_param_names, param_binders, strict=False)
        }

        field_binders: list[tuple[str, Expr]] = []
        local_subst: dict[str, Expr] = dict(param_subst)
        ctor_app_args = [EVar(p_name) for p_name, _ in param_binders]

        for f_name, f_dom in raw_binders:
            # Apply parameter and field substitutions to field domain
            spec_dom = f_dom
            for k, v in local_subst.items():
                spec_dom = substitute_var(spec_dom, k, v)

            unique_f_name = _fresh_name(f_name, used_names)
            local_subst[f_name] = EVar(unique_f_name)

            field_binders.append((unique_f_name, spec_dom))
            ctor_app_args.append(EVar(unique_f_name))

            # If field is recursive (contains inductive type)
            # add an induction hypothesis
            if _contains_inductive(spec_dom, ind_name):
                ih_base = f"ih_{f_name}"
                unique_ih_name = _fresh_name(ih_base, used_names)
                ih_dom = EApp(EVar(motive_var), EVar(unique_f_name))
                field_binders.append((unique_ih_name, ih_dom))

        # Build constructor application instance for the motive conclusion
        ctor_const = EConst(ctor.name, ind_levels)
        ctor_instance = app(ctor_const, *ctor_app_args)
        case_conclusion = EApp(EVar(motive_var), ctor_instance)

        # Wrap case conclusion with field and IH binders (from inside out)
        current_case_type = case_conclusion
        for b_name, b_dom in reversed(field_binders):
            current_case_type = EPi(var=b_name, domain=b_dom, body=current_case_type)

        base_case_name = ctor.name.split(".")[-1] if "." in ctor.name else f"case_{i}"
        case_name = _fresh_name(base_case_name, used_names)
        minor_premises.append((case_name, current_case_type))

    # 6. Terminal type: motive t
    body_expr = EApp(EVar(motive_var), EVar(t_var))
    built_type = EPi(var=t_var, domain=target_expr, body=body_expr)

    # 7. Wrap the type with minor premises for each constructor (reversed)
    for case_name, case_type in reversed(minor_premises):
        built_type = EPi(var=case_name, domain=case_type, body=built_type)

    # 8. Wrap the motive binder around the entire type
    built_type = EPi(var=motive_var, domain=motive_type, body=built_type)

    # 9. Wrap the parameter binders around the entire type
    for p_name, p_dom in reversed(param_binders):
        built_type = EPi(var=p_name, domain=p_dom, body=built_type)

    return RecursorDeclaration(
        name=rec_name,
        level_params=level_params,
        type=built_type,
        inductive_name=ind_name,
        num_params=num_params,
        num_indices=num_indices,
        num_minors=num_minors,
    )


def _contains_inductive(expr: Expr, ind_name: str) -> bool:
    """Check if an expression refers to the given inductive type name."""
    head, _ = decompose_app(expr)
    if isinstance(head, EConst) and head.name == ind_name:
        return True
    match expr:
        case EApp(fn, arg):
            return (
                _contains_inductive(fn, ind_name)
                or _contains_inductive(arg, ind_name)
            )
        case EPi(_, domain, body):
            return (
                _contains_inductive(domain, ind_name)
                or _contains_inductive(body, ind_name)
            )
        case ELam(_, domain, body):
            return (
                _contains_inductive(domain, ind_name)
                or _contains_inductive(body, ind_name)
            )
        case _:
            return False


def _fresh_name(base: str, used_names: set[str]) -> str:
    """Generate a fresh name based on the base name."""
    candidate = base
    counter = 0
    while candidate in used_names:
        counter += 1
        candidate = f"{base}_{counter}"
    used_names.add(candidate)
    return candidate


def declare_quot(env: Environment) -> QuotientDeclaration:
    """Declare the quotient type in the given environment."""
    register_quotient(
        env,
        QuotDeclaration.QUOT_DECLARATION.value,
        QuotDeclaration.QUOT_MK_DECLARATION.value,
        QuotDeclaration.QUOT_LIFT_DECLARATION.value,
        QuotDeclaration.QUOT_IND_DECLARATION.value,
        QuotDeclaration.QUOT_SOUND_DECLARATION.value
    )

    return QuotDeclaration.QUOT_DECLARATION.value
