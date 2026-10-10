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
    QuotDeclaration,
    RecursorDeclaration,
    TheoremDeclaration,
)
from ..errors import KernelTypeError
from .equality import is_def_eq, whnf
from .typecheck import infer_type


def declare(env: Environment, declaration: Declaration) -> None:
    """Declare a new declaration in the environment."""
    env.add(declaration)


# ------------------------------------------------------------------
# Axiom Declaration
# ------------------------------------------------------------------

def declare_axiom(env: Environment, decl: AxiomDeclaration) -> None:
    """Validate and declare an axiom in the environment.

    Args:
        env: Target environment.
        decl: Axiom declaration containing its statement (type).

    Raises:
        KernelTypeError: If the statement does not evaluate to a Sort.

    """
    check_axiom(env, decl)
    declare(env, decl)

def check_axiom(env: Environment, decl: AxiomDeclaration) -> None:
    """Validate that an axiom's statement evaluates to a Sort.

    Raises:
        KernelTypeError: If the statement expression is invalid or does
            not evaluate to a Sort.

    """
    stmt_type_inferred = infer_type(decl.type, {}, {}, env)
    stmt_sort = whnf(stmt_type_inferred, {}, env)
    if not isinstance(stmt_sort, ESort):
        raise KernelTypeError(
            f"Axiom statement '{decl.name}' must evaluate to a Sort, got: "
            f"{stmt_sort}"
        )


# ------------------------------------------------------------------
# Definition Declaration
# ------------------------------------------------------------------

def declare_definition(env: Environment, decl: DefinitionDeclaration) -> None:
    """Validate and declare a definition in the environment.

    Args:
        env: Target environment.
        decl: Definition declaration containing its type and value.

    Raises:
        KernelTypeError: If the value does not type-check or match the declared type.

    """
    check_definition(env, decl)
    declare(env, decl)

def check_definition(env: Environment, decl: DefinitionDeclaration) -> None:
    """Validate that a definition's value matches its declared type.

    Raises:
        KernelTypeError: If the value expression is invalid or its type does
            not definitionally equal the declared type.

    """
    # 1. Ensure the declared type is well-formed and resolves to a Sort.
    type_inferred = infer_type(decl.type, {}, {}, env)
    type_sort = whnf(type_inferred, {}, env)
    if not isinstance(type_sort, ESort):
        raise KernelTypeError(
            f"Type of definition '{decl.name}' must evaluate to a Sort, got: "
            f"{type_sort}"
        )

    # 2. Infer the type of the value expression.
    val_type = infer_type(decl.value, {}, {}, env)

    # 3. Check if inferred value type is definitionally equal to declared type.
    if not is_def_eq(val_type, decl.type, {}, {}, env):
        raise KernelTypeError(
            f"Type mismatch in definition '{decl.name}':\n"
            f"  Expected type : {decl.type}\n"
            f"  Actual type   : {val_type}"
        )


# ------------------------------------------------------------------
# Theorem Declaration
# ------------------------------------------------------------------

def declare_theorem(env: Environment, decl: TheoremDeclaration) -> None:
    """Validate and declare a theorem in the environment.

    Args:
        env: Target environment.
        decl: Theorem declaration containing its statement (type) and proof (value).

    Raises:
        KernelTypeError: If the proof does not type-check or match statement.

    """
    check_theorem(env, decl)
    declare(env, decl)

def check_theorem(env: Environment, decl: TheoremDeclaration) -> None:
    """Validate that a theorem's proof term matches its declared proposition.

    Raises:
        KernelTypeError: If the proof expression is invalid or its type does
            not definitionally equal the declared theorem type.

    """
    # 1. Ensure the declared theorem statement (type) is well-formed.
    stmt_type_inferred = infer_type(decl.type, {}, {}, env)
    stmt_sort = whnf(stmt_type_inferred, {}, env)
    if not isinstance(stmt_sort, ESort):
        raise KernelTypeError(
            f"Theorem statement '{decl.name}' must evaluate to a Sort, got: "
            f"{stmt_sort}"
        )

    # 2. Infer the type of the proof term (value).
    proof_type = infer_type(decl.value, {}, {}, env)

    # 3. Check if inferred proof type is definitionally equal to statement.
    if not is_def_eq(proof_type, decl.type, {}, {}, env):
        raise KernelTypeError(
            f"Type mismatch in theorem '{decl.name}':\n"
            f"  Expected statement : {decl.type}\n"
            f"  Actual proof type  : {proof_type}"
        )


# ------------------------------------------------------------------
# Inductive Declaration
# ------------------------------------------------------------------

def declare_inductive(
    env: Environment,
    decl: InductiveDeclaration,
    ctors: Sequence[ConstructorDeclaration],
    rec: RecursorDeclaration | None = None,
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
    check_inductive(env, decl, ctors, rec)

    declare(env, decl)
    for ctor in ctors:
        declare(env, ctor)
    if rec is not None:
        declare(env, rec)

def check_inductive(
    env: Environment,
    decl: InductiveDeclaration,
    ctors: Sequence[ConstructorDeclaration],
    rec: RecursorDeclaration | None = None,
) -> None:
    """Validate an inductive type, its constructors, and optional recursor.

    Raises:
        KernelTypeError: If any kernel verification rule fails.

    """
    # 1. Validate the main inductive declaration head (must evaluate to a Sort).
    _check_inductive_head(env, decl)

    # 2. Validate all associated constructors.
    for ctor in ctors:
        _check_constructor(env, decl, ctor)

    # 3. Validate the recursor if provided.
    if rec is not None:
        _check_recursor(env, decl, rec)

def _check_inductive_head(env: Environment, decl: InductiveDeclaration) -> None:
    """Check that the inductive declaration's type evaluates to a Sort."""
    sort_expr = infer_type(decl.type, {}, {}, env)

    if not isinstance(whnf(sort_expr, {}, env), ESort):
        raise KernelTypeError(
            f"Type of inductive '{decl.name}' must be a Sort, got: {sort_expr}"
        )

def _check_constructor(
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
        _check_strict_positivity(env, decl.name, curr.domain)
        curr = whnf(curr.body, {}, env)

    # C. Check if target head matches the inductive type being defined.
    head, _ = flatten_app_chain(curr)
    if not isinstance(head, EConst) or head.name != decl.name:
        raise KernelTypeError(
            f"Constructor '{ctor.name}' target type must be '{decl.name}', "
            f"got: {head.name if isinstance(head, EConst) else head}"
        )

def _check_strict_positivity(
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
                f"Strict positivity rule violated: Inductive type '{ind_name}' "
                f"occurs on left-hand side of domain type: {curr.domain}"
            )
        curr = whnf(curr.body, {}, env)

def _check_recursor(
    env: Environment,
    decl: InductiveDeclaration,
    rec: RecursorDeclaration,
) -> None:
    """Validate the recursor type formation and its relation to the inductive type."""
    # 1. Check that the recursor's type evaluates to a Sort.
    rec_sort = infer_type(rec.type, {}, {}, env)
    if not isinstance(whnf(rec_sort, {}, env), ESort):
        raise KernelTypeError(
            f"Recursor '{rec.name}' type must evaluate to a Sort, got: "
            f"{rec_sort}"
        )

    # 2. Check that the recursor's type contains the target Inductive type (decl.name).
    if not _occurs_in(decl.name, rec.type):
        raise KernelTypeError(
            f"Recursor '{rec.name}' type does not target the inductive "
            f"type '{decl.name}'"
        )

    # 3. Check that the recursor's name is prefixed with the Inductive name
    if not rec.name.startswith(f"{decl.name}."):
        raise KernelTypeError(
            f"Recursor name '{rec.name}' must be prefixed with "
            f"inductive name '{decl.name}.'"
        )

def _occurs_in(target_name: str, expr: Expr) -> bool:
    """Recursively check if `target_name` (as EConst) occurs in `expr`."""
    match expr:
        case EConst(name) if name == target_name:
            return True
        case EPi(_, domain, body) | ELam(_, domain, body):
            return _occurs_in(target_name, domain) or _occurs_in(
                target_name, body
            )
        case EApp(fn, arg):
            return _occurs_in(target_name, fn) or _occurs_in(target_name, arg)
        case EMatch(_, discriminee, motive, cases):
            return (
                _occurs_in(target_name, discriminee)
                or _occurs_in(target_name, motive)
                or any(_occurs_in(target_name, c) for c in cases)
            )
        case ESort(_) | EVar(_) | EMetaVar(_):
            return False
        case _:
            return False


# ------------------------------------------------------------------
# Quotient Declaration
# ------------------------------------------------------------------

def declare_quot(
    env: Environment,
    quot_decl: QuotDeclaration,
    mk_decl: QuotDeclaration,
    lift_decl: QuotDeclaration,
    ind_decl: QuotDeclaration,
) -> None:
    """Validate and declare the complete set of quotient primitives.

    Args:
        env: Target environment.
        quot_decl: The Quot type former declaration (variant='quot').
        mk_decl: The Quot.mk constructor declaration (variant='mk').
        lift_decl: The Quot.lift non-dependent recursor (variant='lift').
        ind_decl: The Quot.ind induction principle (variant='ind').

    Raises:
        KernelTypeError: If variant kinds are invalid or any type check fails.

    """
    check_quot(env, quot_decl, mk_decl, lift_decl, ind_decl)

    declare(env, quot_decl)
    declare(env, mk_decl)
    declare(env, lift_decl)
    declare(env, ind_decl)


def check_quot(
    env: Environment,
    quot_decl: QuotDeclaration,
    mk_decl: QuotDeclaration,
    lift_decl: QuotDeclaration,
    ind_decl: QuotDeclaration,
) -> None:
    """Validate that all 4 quotient declarations are valid and form a matching set."""
    decls = [
        ("quot", quot_decl),
        ("mk", mk_decl),
        ("lift", lift_decl),
        ("ind", ind_decl),
    ]

    # 1. Check variant names and ensure each declaration's type evaluates to a Sort.
    for expected_variant, decl in decls:
        if decl.variant != expected_variant:
            raise KernelTypeError(
                f"Expected quotient variant '{expected_variant}', got '{decl.variant}' "
                f"for declaration '{decl.name}'"
            )

        type_inferred = infer_type(decl.type, {}, {}, env)
        type_sort = whnf(type_inferred, {}, env)
        if not isinstance(type_sort, ESort):
            raise KernelTypeError(
                f"Quotient declaration '{decl.name}' must evaluate to a Sort, got: "
                f"{type_sort}"
            )
