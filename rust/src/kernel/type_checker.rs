//! Type checking for expressions in the poussins kernel.
//!
//! Internal kernel module decoupled from `state::Goal` and Python/PyO3 boundaries:
//! - `check` / `check_arc`: verify that an expression has an expected type up to
//!   definitional equality (`infer(expr) ≡ expected_ty`).
//! - `check_is_type` / `check_is_type_arc`: verify that an expression's inferred type
//!   reduces in WHNF to a `Sort`.
//!
//! Stage 3 TODOs:
//! - [Stack safety] Guard deep recursion with `stacker` or an explicit depth limit.

use std::sync::Arc;

use crate::ast::expr::Expr;
use crate::environment::environment::Environment;
use crate::error::KernelError;
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
) -> Result<(), KernelError> {
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
) -> Result<(), KernelError> {
    let mut scope = InferScope::new(local_context);
    let actual_ty = infer_arc(expr, env, &mut scope)?;
    if !is_def_eq_arc(Arc::clone(&actual_ty), Arc::clone(expected_ty), env) {
        return Err(KernelError::TypeMismatch {
            expected: (**expected_ty).clone(),
            actual: (*actual_ty).clone(),
            context_expr: Some((**expr).clone()),
        });
    }
    Ok(())
}

/// Check whether `ty` is a valid type (i.e. its inferred type reduces in WHNF to a `Sort`).
pub(crate) fn check_is_type(
    ty: &Expr,
    env: &Environment,
    local_context: &[(String, Expr)],
) -> Result<(), KernelError> {
    check_is_type_arc(&Arc::new(ty.clone()), env, local_context)
}

/// Core `Arc<Expr>` check that `ty : Sort(u)` for some universe level `u`.
pub(crate) fn check_is_type_arc(
    ty: &Arc<Expr>,
    env: &Environment,
    local_context: &[(String, Expr)],
) -> Result<(), KernelError> {
    let mut scope = InferScope::new(local_context);
    let ty_sort = infer_arc(ty, env, &mut scope)?;
    let reduced = whnf_arc(ty_sort, env);
    if !matches!(*reduced, Expr::Sort(_)) {
        return Err(KernelError::NotASort {
            expr: (**ty).clone(),
            inferred_type: (*reduced).clone(),
        });
    }
    Ok(())
}
