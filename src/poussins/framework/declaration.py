"""Module for declaring axioms, definitions, inductive types, and quotients."""
from __future__ import annotations

from collections.abc import Sequence

from ..ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EPi,
    ESort,
    EVar,
    Expr,
    UnivLevel,
    UnivLevelIMax,
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
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
    infer_type,
    register_axiom,
    register_definition,
    register_inductive,
    register_quotient,
    register_theorem,
    whnf,
)
from ..kernel.univ import normalize_univ_level


def declare_axiom(
    env: Environment,
    name: str,
    statement: Expr,
    level_params: Sequence[str] = (),
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
        level_params=tuple(level_params),
    )
    register_axiom(env, decl)

    return decl


def declare_definition(
    env: Environment,
    name: str,
    type_: Expr,
    value: Expr,
    level_params: Sequence[str] = (),
) -> DefinitionDeclaration:
    """Declare a new definition in the given environment.

    Args:
        env: The environment to which the definition will be added.
        name: The name of the definition.
        type_: The type of the definition.
        value: The value of the definition.
        level_params: Optional tuple of universe level parameters for the definition.

    Returns:
        The created DefinitionDeclaration instance.

    """
    decl = DefinitionDeclaration(
        name=name,
        type=type_,
        value=value,
        level_params=tuple(level_params),
    )
    register_definition(env, decl)

    return decl


def declare_theorem(
    env: Environment,
    name: str,
    statement: Expr,
    term: Expr,
    level_params: Sequence[str] = (),
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
        level_params=tuple(level_params),
    )
    register_theorem(env, decl)

    return decl


def _collect_univ_params_from_level(level: UnivLevel, result: list[str]) -> None:
    """Collect parameter names from a UnivLevel instance."""
    match level:
        case UnivLevelParam(name):
            if name not in result:
                result.append(name)
        case UnivLevelSucc(pred):
            _collect_univ_params_from_level(pred, result)
        case UnivLevelMax(left, right) | UnivLevelIMax(left, right):
            _collect_univ_params_from_level(left, result)
            _collect_univ_params_from_level(right, result)
        case _:
            pass


def _collect_univ_params_from_expr(expr: Expr, result: list[str]) -> None:
    """Collect all UnivLevelParam names present in an expression."""
    match expr:
        case ESort(level):
            _collect_univ_params_from_level(level, result)
        case EConst(_, levels):
            for lvl in levels:
                _collect_univ_params_from_level(lvl, result)
        case EPi(_, domain, body) | ELam(_, domain, body):
            _collect_univ_params_from_expr(domain, result)
            _collect_univ_params_from_expr(body, result)
        case EApp(fn, arg):
            _collect_univ_params_from_expr(fn, result)
            _collect_univ_params_from_expr(arg, result)
        case EMatch(_, discriminee, motive, cases):
            _collect_univ_params_from_expr(discriminee, result)
            _collect_univ_params_from_expr(motive, result)
            for c in cases:
                _collect_univ_params_from_expr(c, result)
        case _:
            pass


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
        case EVar(name):
            if name in ctx:
                var_type = ctx[name]
                if isinstance(var_type, ESort):
                    norm = normalize_univ_level(var_type.level)
                    return isinstance(norm, UnivLevelZero)
            return False
        case EApp():
            head, _ = decompose_app(expr)
            if isinstance(head, EVar) and head.name in ctx:
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
    name: str,
    type_: Expr,
    constructors: Sequence[tuple[str, Expr]],
    level_params: Sequence[str] = (),
) -> InductiveDeclaration:
    """Declare a new inductive type in the given environment.

    Args:
        env: The environment to which the inductive type will be added.
        name: The name of the inductive type.
        type_: The type of the inductive.
        constructors: A sequence of constructor names and their types.
        level_params: A sequence of level parameters.

    Returns:
        The declared InductiveDeclaration.

    """
    if not level_params:
        inferred_levels: list[str] = []
        _collect_univ_params_from_expr(type_, inferred_levels)
        for _, c_type in constructors:
            _collect_univ_params_from_expr(c_type, inferred_levels)
        level_params = tuple(inferred_levels)

    inductive_decl = InductiveDeclaration(
        name=name,
        level_params=tuple(level_params),
        type=type_,
        constructor_names=tuple(c_name for c_name, _ in constructors),
        recursor_names=(f"{name}.rec",),
    )

    constructor_decls = [
        _build_constructor(c_name, c_type, name, tuple(level_params))
        for c_name, c_type in constructors
    ]

    recursor_decl = _build_recursor(
        inductive_decl,
        constructor_decls,
        env=env,
    )

    register_inductive(
        env,
        inductive_decl,
        constructor_decls,
        recursor_decl,
    )

    return inductive_decl

def _build_constructor(
    c_name: str,
    c_type: Expr,
    inductive_name: str,
    inductive_level_params: tuple[str, ...],
) -> ConstructorDeclaration:
    """Build an individual ConstructorDeclaration."""
    ctor_levels: list[str] = []
    _collect_univ_params_from_expr(c_type, ctor_levels)
    merged_ctor_levels = tuple(
        dict.fromkeys(list(inductive_level_params) + ctor_levels)
    )
    return ConstructorDeclaration(
        name=c_name,
        level_params=merged_ctor_levels,
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
    _collect_univ_params_from_expr(inductive_decl.type, base_level_params)
    for ctor in constructor_decls:
        for lp in ctor.level_params:
            if lp not in base_level_params:
                base_level_params.append(lp)
        _collect_univ_params_from_expr(ctor.type, base_level_params)

    used_names: set[str] = set(base_level_params)

    ind_binders: list[tuple[str, Expr]] = []
    curr = inductive_decl.type
    while isinstance(curr, EPi):
        ind_binders.append((curr.var, curr.domain))
        curr = curr.body
    target_sort = curr

    if not constructor_decls:
        num_params = len(ind_binders)
    else:
        match_count = len(ind_binders)
        for ctor in constructor_decls:
            c_curr = ctor.type
            c_binders: list[tuple[str, Expr]] = []
            while isinstance(c_curr, EPi):
                c_binders.append((c_curr.var, c_curr.domain))
                c_curr = c_curr.body
            _, c_args = decompose_app(c_curr)
            k = 0
            while (
                k < len(ind_binders)
                and k < len(c_binders)
                and k < len(c_args)
            ):
                arg = c_args[k]
                expected_var = c_binders[k][0]
                if isinstance(arg, EVar) and arg.name == expected_var:
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

    param_binders: list[tuple[str, Expr]] = []
    for p_var, p_dom in ind_binders[:num_params]:
        p_name = _fresh_name(p_var, used_names)
        param_binders.append((p_name, p_dom))

    index_binders: list[tuple[str, Expr]] = []
    for i_var, i_dom in ind_binders[num_params:]:
        i_name = _fresh_name(i_var, used_names)
        index_binders.append((i_name, i_dom))

    ind_levels = tuple(
        UnivLevelParam(lp)
        for lp in (
            inductive_decl.level_params
            if inductive_decl.level_params
            else base_level_params
        )
    )
    ind_param_expr = EConst(ind_name, ind_levels)
    for p_name, _ in param_binders:
        ind_param_expr = EApp(ind_param_expr, EVar(p_name))
    target_expr = ind_param_expr
    for i_name, _ in index_binders:
        target_expr = EApp(target_expr, EVar(i_name))

    motive_var = _fresh_name("motive", used_names)
    t_var = _fresh_name("t", used_names)

    motive_body = EPi(var=t_var, domain=target_expr, body=motive_sort)
    for i_name, i_dom in reversed(index_binders):
        motive_body = EPi(var=i_name, domain=i_dom, body=motive_body)
    motive_type = motive_body

    num_minors = len(constructor_decls)

    minor_premises: list[tuple[str, Expr]] = []
    for i, ctor in enumerate(constructor_decls):
        ctor_levels = tuple(
            UnivLevelParam(lp)
            for lp in (
                ctor.level_params
                if ctor.level_params
                else base_level_params
            )
        )
        ctor_curr = ctor.type
        raw_ctor_binders: list[tuple[str, Expr]] = []
        while isinstance(ctor_curr, EPi):
            raw_ctor_binders.append((ctor_curr.var, ctor_curr.domain))
            ctor_curr = ctor_curr.body
        ctor_target = ctor_curr
        _, ctor_target_args = decompose_app(ctor_target)
        ctor_indices = ctor_target_args[num_params:]

        raw_param_names = [name for name, _ in raw_ctor_binders[:num_params]]
        raw_field_binders = raw_ctor_binders[num_params:]

        param_subst: dict[str, Expr] = {
            c_p_name: EVar(p_name)
            for c_p_name, (p_name, _) in zip(
                raw_param_names, param_binders, strict=False
            )
        }
        field_binders: list[tuple[str, Expr]] = []
        local_subst: dict[str, Expr] = dict(param_subst)
        ctor_app_args = [EVar(p_name) for p_name, _ in param_binders]

        for f_name, f_dom in raw_field_binders:
            spec_dom = f_dom
            for k, v in local_subst.items():
                spec_dom = substitute_var(spec_dom, k, v)
            unique_f_name = _fresh_name(f_name, used_names)
            local_subst[f_name] = EVar(unique_f_name)
            field_binders.append((unique_f_name, spec_dom))
            ctor_app_args.append(EVar(unique_f_name))

            if _contains_inductive(spec_dom, ind_name):
                ih_base = f"ih_{f_name}"
                unique_ih_name = _fresh_name(ih_base, used_names)
                _, rec_args = decompose_app(spec_dom)
                rec_indices = rec_args[num_params:] if len(rec_args) >= num_params else []
                ih_dom = app(
                    EVar(motive_var),
                    *rec_indices,
                    EVar(unique_f_name),
                )
                field_binders.append((unique_ih_name, ih_dom))

        ctor_const = EConst(ctor.name, ctor_levels)
        ctor_instance = app(ctor_const, *ctor_app_args)

        spec_ctor_indices = []
        for idx_expr in ctor_indices:
            spec_idx = idx_expr
            for k, v in local_subst.items():
                spec_idx = substitute_var(spec_idx, k, v)
            spec_ctor_indices.append(spec_idx)

        case_conclusion = app(
            EVar(motive_var),
            *spec_ctor_indices,
            ctor_instance,
        )

        current_case_type = case_conclusion
        for b_name, b_dom in reversed(field_binders):
            current_case_type = EPi(var=b_name, domain=b_dom, body=current_case_type)

        base_case_name = (
            ctor.name.split(".")[-1] if "." in ctor.name else f"case_{i}"
        )
        case_name = _fresh_name(base_case_name, used_names)
        minor_premises.append((case_name, current_case_type))

    body_expr = app(
        EVar(motive_var),
        *[EVar(i_name) for i_name, _ in index_binders],
        EVar(t_var),
    )
    built_type = EPi(var=t_var, domain=target_expr, body=body_expr)
    for i_name, i_dom in reversed(index_binders):
        built_type = EPi(var=i_name, domain=i_dom, body=built_type)

    for case_name, case_type in reversed(minor_premises):
        built_type = EPi(var=case_name, domain=case_type, body=built_type)

    built_type = EPi(var=motive_var, domain=motive_type, body=built_type)

    for p_name, p_dom in reversed(param_binders):
        built_type = EPi(var=p_name, domain=p_dom, body=built_type)

    return RecursorDeclaration(
        name=rec_name,
        level_params=rec_level_params,
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
        QuotDeclaration.QUOT_SOUND_DECLARATION.value,
    )

    return QuotDeclaration.QUOT_DECLARATION.value
