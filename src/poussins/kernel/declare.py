"""Kernel-level validation and declaration processing."""
from __future__ import annotations

from collections.abc import Sequence

from ..ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
    flatten_app_chain,
)
from ..environment import (
    AxiomDeclaration,
    ConstructorDeclaration,
    Declaration,
    DefinitionDeclaration,
    Environment,
    InductiveDeclaration,
    QuotientDeclaration,
    RecursorDeclaration,
    TheoremDeclaration,
)
from ..errors import KernelTypeError
from .equality import is_def_eq, whnf
from .typecheck import infer_type


# ------------------------------------------------------------------
# Axiom Declaration
# ------------------------------------------------------------------
def register_axiom(env: Environment, decl: AxiomDeclaration) -> None:
    """Validate and declare an axiom in the environment.

    Args:
        env: Target environment.
        decl: Axiom declaration containing its statement (type).

    Raises:
        KernelTypeError: If the statement does not evaluate to a Sort.

    """
    _register_axiom_on_staging(env, decl, with_commit=True)

def validate_axiom(env: Environment, decl: AxiomDeclaration) -> None:
    """Validate that an axiom's statement evaluates to a Sort.

    Raises:
        KernelTypeError: If the statement expression is invalid or
            does not evaluate to a Sort.

    """
    _register_axiom_on_staging(env, decl, with_commit=False)


def _register_axiom_on_staging(
    env: Environment,
    decl: AxiomDeclaration,
    *,
    with_commit: bool
) -> None:
    """Validate an axiom declaration and optionally commit to the environment."""
    staged_decls: list[Declaration] = [decl]

    stage_id = env.stage(declarations=staged_decls)
    staging_env = env.get_staging(stage_id)

    try:
        stmt_type_inferred = infer_type(decl.type, {}, {}, staging_env)
        stmt_sort = whnf(stmt_type_inferred, {}, staging_env)
        if not isinstance(stmt_sort, ESort):
            raise KernelTypeError(
                f"Axiom statement '{decl.name}' must evaluate to a Sort, got: "
                f"{stmt_sort}"
            )

        if with_commit:
            env.commit(stage_id)
        else:
            env.rollback(stage_id)
    except Exception:
        env.rollback(stage_id)
        raise


# ------------------------------------------------------------------
# Definition Declaration
# ------------------------------------------------------------------
def register_definition(env: Environment, decl: DefinitionDeclaration) -> None:
    """Validate and declare a definition in the environment.

    Args:
        env: Target environment.
        decl: Definition declaration containing its type and value.

    Raises:
        KernelTypeError: If the value does not type-check or
            match the declared type.

    """
    _register_definition_on_staging(env, decl, with_commit=True)

def validate_definition(env: Environment, decl: DefinitionDeclaration) -> None:
    """Validate that a definition's value matches its declared type.

    Raises:
        KernelTypeError: If the value expression is invalid or its type
            does not definitionally equal the declared type.

    """
    _register_definition_on_staging(env, decl, with_commit=False)

def _register_definition_on_staging(
    env: Environment,
    decl: DefinitionDeclaration,
    *,
    with_commit: bool
) -> None:
    """Validate a definition declaration, optionally committing to the environment."""
    staged_decls: list[Declaration] = [decl]

    stage_id = env.stage(declarations=staged_decls)
    staging_env = env.get_staging(stage_id)

    try:
        # 1. Ensure the declared type is well-formed and resolves to a Sort.
        type_inferred = infer_type(decl.type, {}, {}, staging_env)
        type_sort = whnf(type_inferred, {}, staging_env)
        if not isinstance(type_sort, ESort):
            raise KernelTypeError(
                f"Type of definition '{decl.name}' must evaluate to a "
                f"Sort, got: {type_sort}"
            )

        # 2. Infer the type of the value expression.
        val_type = infer_type(decl.value, {}, {}, staging_env)

        # 3. Check if inferred value type is definitionally equal to declared type.
        if not is_def_eq(val_type, decl.type, {}, {}, staging_env):
            raise KernelTypeError(
                f"Type mismatch in definition '{decl.name}':\n"
                f"  Expected type : {decl.type}\n"
                f"  Actual type   : {val_type}"
            )

        if with_commit:
            env.commit(stage_id)
        else:
            env.rollback(stage_id)
    except Exception:
        env.rollback(stage_id)
        raise


# ------------------------------------------------------------------
# Theorem Declaration
# ------------------------------------------------------------------
def register_theorem(env: Environment, decl: TheoremDeclaration) -> None:
    """Validate and declare a theorem in the environment.

    Args:
        env: Target environment.
        decl: Theorem declaration containing its statement (type) and proof (value).

    Raises:
        KernelTypeError: If the proof does not type-check or match statement.

    """
    _register_theorem_on_staging(env, decl, with_commit=True)

def validate_theorem(env: Environment, decl: TheoremDeclaration) -> None:
    """Validate that a theorem's proof term matches its declared proposition.

    Raises:
        KernelTypeError: If the proof expression is invalid or its type
            does not definitionally equal the declared theorem type.

    """
    _register_theorem_on_staging(env, decl, with_commit=False)

def _register_theorem_on_staging(
    env: Environment,
    decl: TheoremDeclaration,
    *,
    with_commit: bool
) -> None:
    """Validate a theorem declaration, optionally committing to the environment."""
    staged_decls: list[Declaration] = [decl]

    stage_id = env.stage(declarations=staged_decls)
    staging_env = env.get_staging(stage_id)

    try:
        # 1. Ensure the declared theorem statement (type) is well-formed.
        stmt_type_inferred = infer_type(decl.type, {}, {}, staging_env)
        stmt_sort = whnf(stmt_type_inferred, {}, staging_env)
        if not isinstance(stmt_sort, ESort):
            raise KernelTypeError(
                f"Theorem statement '{decl.name}' must evaluate to a Sort, got: "
                f"{stmt_sort}"
            )

        # 2. Infer the type of the proof term (value).
        proof_type = infer_type(decl.value, {}, {}, staging_env)

        # 3. Check if inferred proof type is definitionally equal to statement.
        if not is_def_eq(proof_type, decl.type, {}, {}, staging_env):
            raise KernelTypeError(
                f"Type mismatch in theorem '{decl.name}':\n"
                f"  Expected statement : {decl.type}\n"
                f"  Actual proof type  : {proof_type}"
            )

        if with_commit:
            env.commit(stage_id)
        else:
            env.rollback(stage_id)
    except Exception:
        env.rollback(stage_id)
        raise


# ------------------------------------------------------------------
# Inductive Declaration
# ------------------------------------------------------------------
def register_inductive(
    env: Environment,
    decl: InductiveDeclaration,
    ctors: Sequence[ConstructorDeclaration],
    rec: RecursorDeclaration
) -> None:
    """Validate and declare an inductive type, its constructors, and recursor.

    Args:
        env: Target environment.
        decl: Inductive type declaration (e.g., Nat, List).
        ctors: List of constructor declarations (e.g., zero/succ, nil/cons).
        rec: Recursor declaration (e.g., Nat.rec).

    Raises:
        KernelTypeError: If type checking, positivity check, or recursor rules fail.

    """
    _register_inductive_on_staging(env, decl, ctors, rec, with_commit=True)

def validate_inductive(
    env: Environment,
    decl: InductiveDeclaration,
    ctors: Sequence[ConstructorDeclaration],
    rec: RecursorDeclaration
) -> None:
    """Validate an inductive type, its constructors, and optional recursor.

    Raises:
        KernelTypeError: If any kernel verification rule fails.

    """
    _register_inductive_on_staging(env, decl, ctors, rec, with_commit=False)

def _register_inductive_on_staging(
    env: Environment,
    decl: InductiveDeclaration,
    ctors: Sequence[ConstructorDeclaration],
    rec: RecursorDeclaration,
    *,
    with_commit: bool
) -> None:
    """Validate an inductive declaration, optionally committing to the environment."""
    staged_decls: list[Declaration] = [decl, *ctors, rec]

    stage_id = env.stage(declarations=staged_decls)
    staging_env = env.get_staging(stage_id)

    try:
        # 1. Validate the main inductive declaration head (must evaluate to a Sort).
        _validate_inductive_head(staging_env, decl)

        # 2. Validate all associated constructors.
        for ctor in ctors:
            _validate_constructor(staging_env, decl, ctor)

        # 3. Validate the recursor with strict structural checks.
        _validate_recursor(staging_env, decl, ctors, rec)

        if with_commit:
            env.commit(stage_id)
        else:
            env.rollback(stage_id)
    except Exception:
        env.rollback(stage_id)
        raise

def _validate_inductive_head(env: Environment, decl: InductiveDeclaration) -> None:
    """Check that the inductive declaration's type evaluates to a Sort."""
    sort_expr = infer_type(decl.type, {}, {}, env)

    if not isinstance(whnf(sort_expr, {}, env), ESort):
        raise KernelTypeError(
            f"Type of inductive '{decl.name}' must be a Sort, got: "
            f"{sort_expr}"
        )

def _validate_constructor(
    env: Environment,
    decl: InductiveDeclaration,
    ctor: ConstructorDeclaration,
) -> None:
    """Validate constructor type formation, target type, and positivity."""
    # A. Validate constructor type formation.
    ctor_sort = infer_type(ctor.type, {}, {}, env)
    if not isinstance(whnf(ctor_sort, {}, env), ESort):
        raise KernelTypeError(
            f"Constructor '{ctor.name}' type must evaluate to a Sort, got: "
            f"{ctor_sort}"
        )

    # B. Inspect Pi binders to validate Strict Positivity for each domain.
    curr = whnf(ctor.type, {}, env)
    while isinstance(curr, EPi):
        _validate_strict_positivity(env, decl.name, curr.domain)
        curr = whnf(curr.body, {}, env)

    # C. Check if target head matches the inductive type being defined.
    head, _ = flatten_app_chain(curr)
    if not isinstance(head, EConst) or head.name != decl.name:
        raise KernelTypeError(
            f"Constructor '{ctor.name}' target type must be "
            f"'{decl.name}', got: "
            f"{head.name if isinstance(head, EConst) else head}"
        )

def _validate_strict_positivity(
    env: Environment, ind_name: str, domain: Expr
) -> None:
    """Check that the inductive type name doesn't appear non-positively.

    The target inductive type `ind_name` must NOT appear on the domain (left)
    of any nested Pi type within constructor arguments.
    """
    curr = whnf(domain, {}, env)
    while isinstance(curr, EPi):
        # Inductive type MUST NOT appear in domain of argument (left of Pi).
        if _occurs_in(ind_name, curr.domain):
            raise KernelTypeError(
                f"Strict positivity rule violated: Inductive type "
                f"'{ind_name}' occurs on left-hand side of domain "
                f"type: {curr.domain}"
            )
        curr = whnf(curr.body, {}, env)

def _validate_recursor(
    env: Environment,
    decl: InductiveDeclaration,
    ctors: Sequence[ConstructorDeclaration],
    rec: RecursorDeclaration,
) -> None:
    """Validate the recursor declaration."""
    # 1. Check that the recursor's type evaluates to a Sort.
    rec_sort = infer_type(rec.type, {}, {}, env)
    if not isinstance(whnf(rec_sort, {}, env), ESort):
        raise KernelTypeError(
            f"Recursor '{rec.name}' type must evaluate to a Sort, got: {rec_sort}"
        )

    # 2. Check that the recursor's type contains the target Inductive type.
    if not _occurs_in(decl.name, rec.type):
        raise KernelTypeError(
            f"Recursor '{rec.name}' type does not target "
            + f"the inductive type '{decl.name}'"
        )

    # 3. Strict Structural Validation
    curr = whnf(rec.type, {}, env)

    pi_binders = []
    while isinstance(curr, EPi):
        pi_binders.append(curr)
        curr = whnf(curr.body, {}, env)

    expected_min_binders = len(ctors) + 2
    if len(pi_binders) < expected_min_binders:
        raise KernelTypeError(
            f"Recursor '{rec.name}' has invalid structure: expected at least "
            + f"{expected_min_binders} Pi binders "
            + f"(motive + {len(ctors)} minor premises + target), "
            + f"got {len(pi_binders)}"
        )

    target_found = (
        any(_occurs_in(decl.name, b.domain) for b in pi_binders)
        or _occurs_in(decl.name, curr)
    )
    if not target_found:
        raise KernelTypeError(
            f"Recursor '{rec.name}' structure does not properly reference "
            f"inductive type '{decl.name}'"
        )

def _occurs_in(target_name: str, expr: Expr) -> bool:
    """Recursively check if `target_name` (as EConst) occurs in `expr`."""
    match expr:
        case EConst(name=name) if name == target_name:
            return True
        case EPi(_, domain, body) | ELam(_, domain, body):
            return _occurs_in(target_name, domain) or _occurs_in(target_name, body)
        case EApp(fn, arg):
            return _occurs_in(target_name, fn) or _occurs_in(target_name, arg)
        case EMatch(_, discriminee, motive, cases):
            return (
                _occurs_in(target_name, discriminee)
                or _occurs_in(target_name, motive)
                or any(_occurs_in(target_name, c) for c in cases)
            )
        case ESort(_) | EVar(_) | EMetaVar(_) | EConst(_):
            return False
        case _:
            return False


# ------------------------------------------------------------------
# Quotient Declaration
# ------------------------------------------------------------------
def register_quotient(
    env: Environment,
    quot_decl: QuotientDeclaration,
    mk_decl: QuotientDeclaration,
    lift_decl: QuotientDeclaration,
    ind_decl: QuotientDeclaration,
    sound_decl: AxiomDeclaration,
) -> None:
    """Validate and declare the complete set of quotient primitives.

    Args:
        env: Target environment.
        quot_decl: The Quot type former declaration (kind='quot').
        mk_decl: The Quot.mk constructor declaration (kind='mk').
        lift_decl: The Quot.lift non-dependent recursor (kind='lift').
        ind_decl: The Quot.ind induction/elimination principle (kind='ind').
        sound_decl: The Quot.sound axiom declaration (AxiomDeclaration).

    Raises:
        KernelTypeError: If kinds are invalid or any type check fails.

    """
    _register_quotient_on_staging(
        env,
        quot_decl,
        mk_decl,
        lift_decl,
        ind_decl,
        sound_decl,
        with_commit=True,
    )

def validate_quotient(
    env: Environment,
    quot_decl: QuotientDeclaration,
    mk_decl: QuotientDeclaration,
    lift_decl: QuotientDeclaration,
    ind_decl: QuotientDeclaration,
    sound_decl: AxiomDeclaration,
) -> None:
    """Validate that all quotient primitives and the sound axiom form a matching set."""
    _register_quotient_on_staging(
        env,
        quot_decl,
        mk_decl,
        lift_decl,
        ind_decl,
        sound_decl,
        with_commit=False,
    )

def _register_quotient_on_staging(
    env: Environment,
    quot_decl: QuotientDeclaration,
    mk_decl: QuotientDeclaration,
    lift_decl: QuotientDeclaration,
    ind_decl: QuotientDeclaration,
    sound_decl: AxiomDeclaration,
    *,
    with_commit: bool,
) -> None:
    """Validate quotient declarations, optionally committing to the environment."""
    staged_decls: list[Declaration] = [
        quot_decl,
        mk_decl,
        lift_decl,
        ind_decl,
        sound_decl,
    ]
    stage_id = env.stage(declarations=staged_decls)
    staging_env = env.get_staging(stage_id)
    try:
        # 1. Validate Quotient-specific primitives (quot, mk, lift, ind)
        quot_decls = [
            ("type", quot_decl),
            ("mk", mk_decl),
            ("lift", lift_decl),
            ("ind", ind_decl),
        ]
        for expected_kind, decl in quot_decls:
            if decl.kind != expected_kind:
                raise KernelTypeError(
                    f"Expected quotient kind '{expected_kind}', "
                    f"got '{decl.kind}' for declaration '{decl.name}'"
                )
            type_inferred = infer_type(decl.type, {}, {}, staging_env)
            type_sort = whnf(type_inferred, {}, staging_env)
            if not isinstance(type_sort, ESort):
                raise KernelTypeError(
                    f"Quotient declaration '{decl.name}' must evaluate to a "
                    f"Sort, got: {type_sort}"
                )

        # 2. Validate Quot.sound axiom declaration
        sound_type_inferred = infer_type(sound_decl.type, {}, {}, staging_env)
        sound_sort = whnf(sound_type_inferred, {}, staging_env)
        if not isinstance(sound_sort, ESort):
            raise KernelTypeError(
                f"Axiom statement '{sound_decl.name}' must evaluate to a Sort, got: "
                f"{sound_sort}"
            )

        if with_commit:
            env.commit(stage_id)
        else:
            env.rollback(stage_id)
    except Exception:
        env.rollback(stage_id)
        raise
