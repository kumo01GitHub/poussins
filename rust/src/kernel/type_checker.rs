//! Type checking for expressions and environment declarations in the poussins kernel.
//!
//! Internal kernel module decoupled from `state::Goal` and Python/PyO3 boundaries:
//! - `check` / `check_arc`: verify that an expression has an expected type up to
//!   definitional equality (`infer(expr) ≡ expected_ty`).
//! - `check_is_type`: verify that an expression's inferred type reduces in WHNF to a `Sort`.
//! - `check_declaration`: validate well-typedness of `Declaration` items (`Definition`,
//!   `Axiom`, `Inductive`, `Constructor`, `Recursor`) before adding them to `Environment`.
//!
//! Stage 2 / Stage 3 TODOs:
//! - [Error design] Replace `bool` returns with structured kernel errors under `errors/`
//!   once designed (distinguishing type mismatch, ill-formed sort, duplicate universe params, etc.).
//! - [Inductive / Recursor rules] Enforce strict positivity on `InductiveDecl` constructors
//!   and verify `RecursorRule` right-hand sides (`rhs`) against motive/minor types.
//! - [Universe parameter check] Verify that all `UnivLevel::Param` occurrences inside
//!   declaration `ty` / `value` are bound in `level_params`.
//! - [Stack safety] Guard deep recursion with `stacker` or an explicit depth limit.

use std::collections::HashSet;
use std::sync::Arc;

use crate::ast::expr::Expr;
use crate::environment::declaration::Declaration;
use crate::environment::environment::Environment;
use crate::kernel::equality::is_def_eq_arc;
use crate::kernel::inference::{infer_arc, InferScope};
use crate::kernel::reduction::whnf_arc;

// ---------------------------------------------------------------------------
// Expression Type Checking
// ---------------------------------------------------------------------------

/// Check whether `expr` has type `expected_ty` (up to definitional equality)
/// under `env` and an ordered slice of local hypotheses `local_context`.
pub(crate) fn check(
    expr: &Expr,
    expected_ty: &Expr,
    env: &Environment,
    local_context: &[(String, Expr)],
) -> bool {
    check_arc(
        &Arc::new(expr.clone()),
        &Arc::new(expected_ty.clone()),
        env,
        local_context,
    )
}

/// Core `Arc<Expr>` type check: infer `expr`'s type and compare with `expected_ty`.
pub(crate) fn check_arc(
    expr: &Arc<Expr>,
    expected_ty: &Arc<Expr>,
    env: &Environment,
    local_context: &[(String, Expr)],
) -> bool {
    let mut scope = InferScope::new(local_context);
    let Some(actual_ty) = infer_arc(expr, env, &mut scope) else {
        return false;
    };
    is_def_eq_arc(actual_ty, Arc::clone(expected_ty), env)
}

/// Check whether `ty` is a valid type (i.e. its inferred type reduces in WHNF to a `Sort`).
pub(crate) fn check_is_type(
    ty: &Expr,
    env: &Environment,
    local_context: &[(String, Expr)],
) -> bool {
    check_is_type_arc(&Arc::new(ty.clone()), env, local_context)
}

/// Core `Arc<Expr>` check that `ty : Sort(u)` for some universe level `u`.
pub(crate) fn check_is_type_arc(
    ty: &Arc<Expr>,
    env: &Environment,
    local_context: &[(String, Expr)],
) -> bool {
    let mut scope = InferScope::new(local_context);
    let Some(ty_sort) = infer_arc(ty, env, &mut scope) else {
        return false;
    };
    matches!(*whnf_arc(ty_sort, env), Expr::Sort(_))
}

// ---------------------------------------------------------------------------
// Declaration Type Checking
// ---------------------------------------------------------------------------

/// Check that universe level parameter names contain no duplicates.
fn has_unique_level_params(level_params: &[String]) -> bool {
    let mut seen = HashSet::with_capacity(level_params.len());
    level_params.iter().all(|p| seen.insert(p.as_str()))
}

/// Validate a `Declaration` before inserting it into `env`.
///
/// Stage 1 checks:
/// - No duplicate universe level parameters (`level_params`).
/// - Declaration type (`ty`) is a valid `Sort` at top-level (`local_context = &[]`).
/// - For `DefinitionDecl`, `value` has type `ty` (`check(&def.value, &def.ty, env, &[])`).
pub(crate) fn check_declaration(decl: &Declaration, env: &Environment) -> bool {
    match decl {
        Declaration::Definition(def) => {
            has_unique_level_params(&def.level_params)
                && check_is_type(&def.ty, env, &[])
                && check(&def.value, &def.ty, env, &[])
        }
        Declaration::Axiom(ax) => {
            has_unique_level_params(&ax.level_params) && check_is_type(&ax.ty, env, &[])
        }
        Declaration::Inductive(ind) => {
            has_unique_level_params(&ind.level_params) && check_is_type(&ind.ty, env, &[])
        }
        Declaration::Constructor(ctor) => {
            has_unique_level_params(&ctor.level_params) && check_is_type(&ctor.ty, env, &[])
        }
        Declaration::Recursor(rec) => {
            has_unique_level_params(&rec.level_params) && check_is_type(&rec.ty, env, &[])
        }
    }
}
