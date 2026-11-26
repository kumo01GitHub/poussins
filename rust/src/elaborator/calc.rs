//! Metavariable-aware calculation facade for the poussins elaborator.
//!
//! Bridges `state::Snapshot` (goal/metavariable declarations and assignments) and `kernel`
//! (pure reduction, type inference, and definitional equality):
//! - `instantiate_mvars`: transitively unfold solved expression metavariables
//!   with cycle protection and `Arc` sharing.
//! - `whnf`: instantiate metavariables and reduce to Weak Head Normal Form.
//! - `is_def_eq`: check definitional equality after metavariable instantiation.
//! - `infer`: infer the type of expressions containing metavariables by unfolding
//!   assigned goals and resolving open goal statements from `Snapshot::goals`.

use std::collections::HashSet;
use std::sync::Arc;

use crate::ast::expr::{Expr, Literal};
use crate::environment::environment::Environment;
use crate::error::KernelError;
use crate::kernel::equality::is_def_eq_arc;
use crate::kernel::inference::{infer_arc_with_mvar, InferScope};
use crate::kernel::reduction::whnf_arc as kernel_whnf_arc;
use crate::state::snapshot::Snapshot;

// ---------------------------------------------------------------------------
// Transitive Metavariable Instantiation
// ---------------------------------------------------------------------------

/// Transitively instantiate all solved expression metavariables in `expr`.
///
/// Reuses existing `Arc` nodes whenever subtrees contain no solved metavariables.
pub fn instantiate_mvars(expr: &Expr, snapshot: &Snapshot) -> Result<Expr, KernelError> {
    let arc_res = instantiate_mvars_arc(&Arc::new(expr.clone()), snapshot)?;
    Ok(Arc::try_unwrap(arc_res).unwrap_or_else(|a| (*a).clone()))
}

/// `Arc<Expr>` version of `instantiate_mvars` preserving pointer identity when unchanged.
pub(crate) fn instantiate_mvars_arc(
    expr: &Arc<Expr>,
    snapshot: &Snapshot,
) -> Result<Arc<Expr>, KernelError> {
    let mut visited = HashSet::new();
    instantiate_mvars_inner(expr, snapshot, &mut visited)
}

fn instantiate_mvars_inner(
    expr: &Arc<Expr>,
    snapshot: &Snapshot,
    visited: &mut HashSet<String>,
) -> Result<Arc<Expr>, KernelError> {
    match &**expr {
        Expr::BVar(_) | Expr::FVar(_) | Expr::Sort(_) | Expr::Const(_) => Ok(Arc::clone(expr)),
        Expr::MVar(m) => {
            if let Some(assigned) = snapshot
                .goals
                .get(&m.id)
                .and_then(|goal| goal.assignment.as_ref())
            {
                if !visited.insert(m.id.clone()) {
                    return Err(KernelError::InvalidValue {
                        message: format!(
                            "Cyclic metavariable assignment detected for '?{}'",
                            m.id
                        ),
                        expr: Some((**expr).clone()),
                    });
                }
                let res = instantiate_mvars_inner(&Arc::new(assigned.clone()), snapshot, visited);
                visited.remove(&m.id);
                res
            } else {
                Ok(Arc::clone(expr))
            }
        }
        Expr::App(app) => {
            let f = instantiate_mvars_inner(&app.f, snapshot, visited)?;
            let arg = instantiate_mvars_inner(&app.arg, snapshot, visited)?;
            if Arc::ptr_eq(&app.f, &f) && Arc::ptr_eq(&app.arg, &arg) {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::app(f, arg)))
            }
        }
        Expr::Lam(lam) => {
            let t = instantiate_mvars_inner(&lam.t, snapshot, visited)?;
            let body = instantiate_mvars_inner(&lam.body, snapshot, visited)?;
            if Arc::ptr_eq(&lam.t, &t) && Arc::ptr_eq(&lam.body, &body) {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::lam(lam.var.clone(), t, body)))
            }
        }
        Expr::Pi(pi) => {
            let t = instantiate_mvars_inner(&pi.t, snapshot, visited)?;
            let body = instantiate_mvars_inner(&pi.body, snapshot, visited)?;
            if Arc::ptr_eq(&pi.t, &t) && Arc::ptr_eq(&pi.body, &body) {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::pi(pi.var.clone(), t, body)))
            }
        }
        Expr::Let(let_expr) => {
            let t = instantiate_mvars_inner(&let_expr.t, snapshot, visited)?;
            let value = instantiate_mvars_inner(&let_expr.value, snapshot, visited)?;
            let body = instantiate_mvars_inner(&let_expr.body, snapshot, visited)?;
            if Arc::ptr_eq(&let_expr.t, &t)
                && Arc::ptr_eq(&let_expr.value, &value)
                && Arc::ptr_eq(&let_expr.body, &body)
            {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::let_(
                    let_expr.var.clone(),
                    t,
                    value,
                    body,
                )))
            }
        }
        Expr::Lit(lit) => match &lit.lit {
            Literal::Nat(_) | Literal::Float(_) | Literal::String(_) => Ok(Arc::clone(expr)),
            Literal::Array(items) => {
                let mut changed = false;
                let mut new_items = Vec::with_capacity(items.len());
                for item in items {
                    let item_arc = Arc::new(item.clone());
                    let inst = instantiate_mvars_inner(&item_arc, snapshot, visited)?;
                    if !Arc::ptr_eq(&item_arc, &inst) {
                        changed = true;
                    }
                    new_items.push(Arc::try_unwrap(inst).unwrap_or_else(|a| (*a).clone()));
                }
                if changed {
                    Ok(Arc::new(Expr::lit(Literal::Array(new_items))))
                } else {
                    Ok(Arc::clone(expr))
                }
            }
        },
    }
}

// ---------------------------------------------------------------------------
// Metavariable-Aware WHNF & Definitional Equality
// ---------------------------------------------------------------------------

/// Reduce `expr` to Weak Head Normal Form after instantiating solved metavariables.
pub fn whnf(expr: &Expr, env: &Environment, snapshot: &Snapshot) -> Result<Expr, KernelError> {
    let arc_res = whnf_arc(&Arc::new(expr.clone()), env, snapshot)?;
    Ok(Arc::try_unwrap(arc_res).unwrap_or_else(|a| (*a).clone()))
}

/// `Arc<Expr>` version of `whnf`.
pub(crate) fn whnf_arc(
    expr: &Arc<Expr>,
    env: &Environment,
    snapshot: &Snapshot,
) -> Result<Arc<Expr>, KernelError> {
    let inst = instantiate_mvars_arc(expr, snapshot)?;
    Ok(kernel_whnf_arc(inst, env))
}

/// Check definitional equality of `t` and `s` after instantiating solved metavariables.
pub fn is_def_eq(
    t: &Expr,
    s: &Expr,
    env: &Environment,
    snapshot: &Snapshot,
) -> Result<bool, KernelError> {
    let t_inst = instantiate_mvars_arc(&Arc::new(t.clone()), snapshot)?;
    let s_inst = instantiate_mvars_arc(&Arc::new(s.clone()), snapshot)?;
    Ok(is_def_eq_arc(t_inst, s_inst, env))
}

// ---------------------------------------------------------------------------
// Metavariable-Aware Type Inference
// ---------------------------------------------------------------------------

/// Infer the type of `expr` under `env`, `local_context`, and `snapshot`.
///
/// Instantiates solved goals first, then delegates AST traversal to
/// `kernel::inference::infer_arc_with_mvar`, resolving unassigned `?id` nodes
/// from `snapshot.goals.get(id).statement`.
pub fn infer(
    expr: &Expr,
    env: &Environment,
    local_context: &[(String, Expr)],
    snapshot: &Snapshot,
) -> Result<Expr, KernelError> {
    let inst = instantiate_mvars_arc(&Arc::new(expr.clone()), snapshot)?;
    let mut scope = InferScope::new(local_context);
    let mut resolve_goal = |mvar_id: &str| -> Result<Arc<Expr>, KernelError> {
        let goal = snapshot
            .goals
            .get(mvar_id)
            .ok_or_else(|| KernelError::InvalidValue {
                message: format!("Unknown goal/metavariable '?{mvar_id}'"),
                expr: Some(Expr::mvar(mvar_id.to_string())),
            })?;
        instantiate_mvars_arc(&Arc::new(goal.statement.clone()), snapshot)
    };
    let ty = infer_arc_with_mvar(&inst, env, &mut scope, &mut resolve_goal)?;
    let ty_inst = instantiate_mvars_arc(&ty, snapshot)?;
    Ok(Arc::try_unwrap(ty_inst).unwrap_or_else(|a| (*a).clone()))
}
