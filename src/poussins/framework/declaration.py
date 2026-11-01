"""Module for declaring axioms, definitions, inductive types, and quotients."""
from __future__ import annotations

from collections.abc import Sequence

from ..ast import (
    EApp,
    EConst,
    EFVar,
    ELam,
    EPi,
    ESort,
    Expr,
    UnivLevelParam,
    UnivLevelZero,
    app,
    collect_univ_level_params,
    decompose_app,
    lam,
    pi,
    substitute_var,
    univ_levels,
)
from ..environment import (
    AxiomDeclaration,
    AxiomSpec,
    ConstructorDeclaration,
    DefinitionDeclaration,
    DefinitionSpec,
    Environment,
    InductiveDeclaration,
    InductiveSpec,
    QuotientDeclaration,
    RecursorDeclaration,
    TheoremDeclaration,
    TheoremSpec,
)
from ..environment.library import (
    QUOT_DECLARATION,
    QUOT_IND_DECLARATION,
    QUOT_LIFT_DECLARATION,
    QUOT_MK_DECLARATION,
    QUOT_SOUND_DECLARATION,
)
from ..kernel import (
    infer_type,
    normalize_univ_level,
    register_axiom,
    register_definition,
    register_inductive,
    register_quotient,
    register_theorem,
    whnf,
)
from .bound_var import instantiate_binder_body


def declare_axiom(
    env: Environment,
    spec: AxiomSpec,
) -> AxiomDeclaration:
    """Declare a new axiom in the given environment."""
    decl = AxiomDeclaration(
        name=spec.name,
        type=spec.statement,
        level_params=collect_univ_level_params(spec.statement),
    )
    register_axiom(env, decl)

    return decl


def declare_definition(
    env: Environment,
    spec: DefinitionSpec,
) -> DefinitionDeclaration:
    """Declare a new definition in the given environment."""
    decl = DefinitionDeclaration(
        name=spec.name,
        type=spec.type,
        value=spec.value,
        level_params=collect_univ_level_params(
            spec.value,
            collect_univ_level_params(spec.type)
        ),
    )
    register_definition(env, decl)

    return decl


def declare_theorem(
    env: Environment,
    spec: TheoremSpec,
) -> TheoremDeclaration:
    """Declare a new theorem in the given environment."""
    decl = TheoremDeclaration(
        name=spec.name,
        type=spec.statement,
        value=spec.term,
        level_params=collect_univ_level_params(
            spec.term,
            collect_univ_level_params(spec.statement)
        ),
    )
    register_theorem(env, decl)

    return decl


def _is_prop(
    expr: Expr,
    ctx: dict[str, Expr],
    env: Environment | None,
    ind_name: str,
    ind_is_prop: bool,
) -> bool:
    """Check if the given expression represents a proposition (sort Prop / Sort 0)."""
    if env is not None:
        try:
            t = infer_type(expr, ctx, {}, env)
            s = whnf(t, {}, env)
            if isinstance(s, ESort):
                norm = normalize_univ_level(s.level)
                return isinstance(norm, UnivLevelZero)
        except Exception:  # noqa: S110
            pass
    match expr:
        case ESort(_):
            return False
        case EFVar(name):
            if name in ctx:
                var_type = ctx[name]
                if isinstance(var_type, ESort):
                    norm = normalize_univ_level(var_type.level)
                    return isinstance(norm, UnivLevelZero)
            return False
        case EApp():
            head, _ = decompose_app(expr)
            if isinstance(head, EFVar) and head.name in ctx:
                fn_type = ctx[head.name]
                curr = fn_type
                while isinstance(curr, EPi):
                    curr = curr.body
                if isinstance(curr, ESort):
                    norm = normalize_univ_level(curr.level)
                    return isinstance(norm, UnivLevelZero)
            if isinstance(head, EConst):
                if head.name == ind_name and ind_is_prop:
                    return True
                if env is not None:
                    decl = env.get(head.name)
                    if decl is not None:
                        curr = decl.type
                        while isinstance(curr, EPi):
                            curr = curr.body
                        if isinstance(curr, ESort):
                            norm = normalize_univ_level(curr.level)
                            return isinstance(norm, UnivLevelZero)
        case EPi(_, _, body):
            return _is_prop(body, ctx, env, ind_name, ind_is_prop)
    return False


def declare_inductive(
    env: Environment,
    spec: InductiveSpec,
) -> InductiveDeclaration:
    """Declare a new inductive type in the given environment."""
    level_params = collect_univ_level_params(spec.type)
    for _, c_type in spec.constructors:
        level_params = collect_univ_level_params(c_type, level_params)

    inductive_decl = InductiveDeclaration(
        name=spec.name,
        level_params=level_params,
        type=spec.type,
        constructor_names=tuple(c_name for c_name, _ in spec.constructors),
        recursor_names=(f"{spec.name}.rec",),
    )

    constructor_decls = [
        _build_constructor(c_name, c_type, spec.name, level_params)
        for c_name, c_type in spec.constructors
    ]

    recursor_decl = _build_recursor(
        inductive_decl,
        constructor_decls,
        env=env,
    )
    cases_on_decl = _build_cases_on(
        inductive_decl,
        recursor_decl,
    )

    register_inductive(
        env,
        inductive_decl,
        constructor_decls,
        recursor_decl,
        extra_definitions=(cases_on_decl,),
    )

    return inductive_decl

def _build_constructor(
    c_name: str,
    c_type: Expr,
    inductive_name: str,
    inductive_level_params: tuple[str, ...],
) -> ConstructorDeclaration:
    """Build an individual ConstructorDeclaration."""
    return ConstructorDeclaration(
        name=c_name,
        level_params=collect_univ_level_params(
            c_type,
            inductive_level_params,
        ),
        type=c_type,
        inductive_name=inductive_name,
    )

def _build_recursor(
    inductive_decl: InductiveDeclaration,
    constructor_decls: Sequence[ConstructorDeclaration],
    env: Environment | None = None,
) -> RecursorDeclaration:
    """Build the recursor declaration for an inductive type."""
    ind_name = inductive_decl.name
    rec_name = inductive_decl.recursor_names[0]

    base_level_params: list[str] = list(inductive_decl.level_params)

    used_names: set[str] = set(base_level_params)

    ind_binders, target_sort = _open_pi_binders(inductive_decl.type, used_names)

    if not constructor_decls:
        num_params = len(ind_binders)
    else:
        match_count = len(ind_binders)
        for ctor in constructor_decls:
            opened_binders, ctor_target = _open_pi_binders(ctor.type, used_names=set())
            _, c_args = decompose_app(ctor_target)
            k = 0
            while k < len(ind_binders) and k < len(opened_binders) and k < len(c_args):
                expected_var = opened_binders[k][0]
                arg = c_args[k]
                if isinstance(arg, EFVar) and arg.name == expected_var:
                    k += 1
                else:
                    break
            match_count = min(match_count, k)
        num_params = match_count
    num_indices = max(0, len(ind_binders) - num_params)

    is_prop = False
    if isinstance(target_sort, ESort):
        norm_level = normalize_univ_level(target_sort.level)
        if isinstance(norm_level, UnivLevelZero):
            is_prop = True
    elif env is not None:
        try:
            inferred = infer_type(target_sort, {}, {}, env)
            whnf_sort = whnf(inferred, {}, env)
            if isinstance(whnf_sort, ESort) and isinstance(
                normalize_univ_level(whnf_sort.level), UnivLevelZero
            ):
                is_prop = True
        except Exception:  # noqa: S110
            pass

    has_large_elim = True
    if is_prop:
        if len(constructor_decls) == 0:
            has_large_elim = True
        elif len(constructor_decls) > 1:
            has_large_elim = False
        else:
            has_large_elim = True

    if has_large_elim:
        motive_level = _fresh_name("v", used_names)
        rec_level_params = tuple(base_level_params + [motive_level])
        motive_sort = ESort(UnivLevelParam(motive_level))
    else:
        rec_level_params = tuple(base_level_params)
        motive_sort = ESort(UnivLevelZero())

    param_binders = ind_binders[:num_params]
    index_binders = ind_binders[num_params:]

    ind_param_expr = EConst(ind_name, univ_levels(inductive_decl.level_params))
    for p_name, _ in param_binders:
        ind_param_expr = EApp(ind_param_expr, EFVar(p_name))
    target_expr = ind_param_expr
    for i_name, _ in index_binders:
        target_expr = EApp(target_expr, EFVar(i_name))

    motive_var = _fresh_name("motive", used_names)
    t_var = _fresh_name("t", used_names)

    motive_body = pi(((t_var, target_expr),), motive_sort)
    for i_name, i_dom in reversed(index_binders):
        motive_body = pi(((i_name, i_dom),), motive_body)
    motive_type = motive_body

    num_minors = len(constructor_decls)

    minor_premises: list[tuple[str, Expr]] = []
    for i, ctor in enumerate(constructor_decls):
        opened_binders, ctor_target = _open_pi_binders(ctor.type, used_names)
        ctor_param_binders = opened_binders[:num_params]
        param_subst = {
            ctor_name: EFVar(rec_name)
            for (ctor_name, _), (rec_name, _) in zip(
                ctor_param_binders,
                param_binders,
                strict=False,
            )
        }
        _, ctor_target_args = decompose_app(ctor_target)
        ctor_indices = [
            _substitute_named_many(idx_expr, param_subst)
            for idx_expr in ctor_target_args[num_params:]
        ]
        field_binders: list[tuple[str, Expr]] = []
        ctor_app_args = [EFVar(p_name) for p_name, _ in param_binders]

        for f_name, raw_spec_dom in opened_binders[num_params:]:
            spec_dom = _substitute_named_many(raw_spec_dom, param_subst)
            field_binders.append((f_name, spec_dom))
            ctor_app_args.append(EFVar(f_name))

            if _contains_inductive(spec_dom, ind_name):
                ih_base = f"ih_{f_name}"
                unique_ih_name = _fresh_name(ih_base, used_names)
                _, rec_args = decompose_app(spec_dom)
                rec_indices = (
                    rec_args[num_params:]
                    if len(rec_args) >= num_params else []
                )
                ih_dom = app(
                    EFVar(motive_var),
                    *rec_indices,
                    EFVar(f_name),
                )
                field_binders.append((unique_ih_name, ih_dom))

        ctor_const = EConst(ctor.name, univ_levels(ctor.level_params))
        ctor_instance = app(ctor_const, *ctor_app_args)
        spec_ctor_indices = list(ctor_indices)

        case_conclusion = app(
            EFVar(motive_var),
            *spec_ctor_indices,
            ctor_instance,
        )

        current_case_type = case_conclusion
        for b_name, b_dom in reversed(field_binders):
            current_case_type = pi(((b_name, b_dom),), current_case_type)

        base_case_name = (
            ctor.name.split(".")[-1] if "." in ctor.name else f"case_{i}"
        )
        case_name = _fresh_name(base_case_name, used_names)
        minor_premises.append((case_name, current_case_type))

    body_expr = app(
        EFVar(motive_var),
        *[EFVar(i_name) for i_name, _ in index_binders],
        EFVar(t_var),
    )
    built_type = pi(((t_var, target_expr),), body_expr)
    for i_name, i_dom in reversed(index_binders):
        built_type = pi(((i_name, i_dom),), built_type)

    for case_name, case_type in reversed(minor_premises):
        built_type = pi(((case_name, case_type),), built_type)

    built_type = pi(((motive_var, motive_type),), built_type)

    for p_name, p_dom in reversed(param_binders):
        built_type = pi(((p_name, p_dom),), built_type)

    return RecursorDeclaration(
        name=rec_name,
        level_params=rec_level_params,
        type=built_type,
        inductive_name=ind_name,
        num_params=num_params,
        num_indices=num_indices,
        num_minors=num_minors,
    )


def _build_cases_on(
    inductive_decl: InductiveDeclaration,
    recursor_decl: RecursorDeclaration,
) -> DefinitionDeclaration:
    """Build a `casesOn` definition by reordering recursor arguments."""
    binders, current = _open_pi_binders(recursor_decl.type, used_names=set())

    param_binders = binders[:recursor_decl.num_params]
    motive_binder = binders[recursor_decl.num_params]
    minor_start = recursor_decl.num_params + 1
    minor_end = minor_start + recursor_decl.num_minors
    rec_minor_binders = binders[minor_start:minor_end]
    index_start = minor_end
    index_end = index_start + recursor_decl.num_indices
    index_binders = binders[index_start:index_end]
    major_binder = binders[index_end]

    transformed_minor_binders: list[tuple[str, Expr]] = []
    rec_minor_wrappers: list[Expr] = []

    for case_name, case_type in rec_minor_binders:
        minor_pi_binders, minor_result = _open_pi_binders(case_type, used_names=set())

        visible_minor_binders = [
            (name, domain)
            for name, domain in minor_pi_binders
            if not name.startswith("ih_")
        ]

        transformed_case_type = minor_result
        for var_name, domain in reversed(visible_minor_binders):
            transformed_case_type = pi(((var_name, domain),), transformed_case_type)
        transformed_minor_binders.append((case_name, transformed_case_type))

        wrapped_minor_body = app(
            EFVar(case_name),
            *[EFVar(name) for name, _ in visible_minor_binders],
        )
        wrapped_minor_value: Expr = wrapped_minor_body
        for var_name, domain in reversed(minor_pi_binders):
            wrapped_minor_value = lam(((var_name, domain),), wrapped_minor_value)
        rec_minor_wrappers.append(wrapped_minor_value)

    cases_on_binders = [
        *param_binders,
        *index_binders,
        major_binder,
        motive_binder,
        *transformed_minor_binders,
    ]

    cases_on_type = current
    for var_name, domain in reversed(cases_on_binders):
        cases_on_type = pi(((var_name, domain),), cases_on_type)

    recursor_const = EConst(recursor_decl.name, univ_levels(recursor_decl.level_params))
    recursor_args = [
        *[EFVar(name) for name, _ in param_binders],
        EFVar(motive_binder[0]),
        *rec_minor_wrappers,
        *[EFVar(name) for name, _ in index_binders],
        EFVar(major_binder[0]),
    ]
    cases_on_value: Expr = app(recursor_const, *recursor_args)
    for var_name, domain in reversed(cases_on_binders):
        cases_on_value = lam(((var_name, domain),), cases_on_value)

    return DefinitionDeclaration(
        name=f"{inductive_decl.name}.casesOn",
        level_params=recursor_decl.level_params,
        type=cases_on_type,
        value=cases_on_value,
    )


def _open_pi_binders(
    expr: Expr,
    used_names: set[str]
) -> tuple[list[tuple[str, Expr]], Expr]:
    """Open Pi binders into fresh EFVar names and return opened binders with body."""
    binders: list[tuple[str, Expr]] = []
    current = expr
    local_used = set(used_names)
    while isinstance(current, EPi):
        opened_name = _fresh_name(current.var, local_used)
        binders.append((opened_name, current.domain))
        current = instantiate_binder_body(current.body, EFVar(opened_name))
    used_names.update(local_used)
    return binders, current


def _substitute_named_many(expr: Expr, subst: dict[str, Expr]) -> Expr:
    """Apply a sequence of named substitutions to an expression."""
    result = expr
    for name, replacement in subst.items():
        result = substitute_var(result, name, replacement)
    return result


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
        QUOT_DECLARATION,
        QUOT_MK_DECLARATION,
        QUOT_LIFT_DECLARATION,
        QUOT_IND_DECLARATION,
        QUOT_SOUND_DECLARATION,
    )

    return QUOT_DECLARATION
