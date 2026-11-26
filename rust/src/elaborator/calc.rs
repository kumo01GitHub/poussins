//! Metavariable-aware calculation facade for the poussins elaborator.
//!
//! Bridges `state::Snapshot` (goal/metavariable declarations and assignments) and `kernel`
//! (pure reduction, type inference, and definitional equality):
//! - `instantiate_mvars`: transitively unfold solved expression metavariables
//!   with cycle protection and `Arc` sharing.
//! - `whnf`: instantiate metavariables and reduce to Weak Head Normal Form.
//! - `is_def_eq`: check definitional equality after metavariable instantiation.
//! - `infer`: infer the type of expressions containing unassigned metavariables
//!   by consulting `Snapshot::goals`.

use std::collections::HashSet;
use std::sync::Arc;

use crate::ast::expr::{Expr, Literal};
use crate::ast::ops::{bind, instantiate_bvar, instantiate_univ_level};
use crate::ast::univ_level::UnivLevel;
use crate::environment::declaration::Declaration;
use crate::environment::environment::Environment;
use crate::error::KernelError;
use crate::kernel::equality::is_def_eq_arc;
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

struct ElabScope<'a> {
    outer: &'a [(String, Expr)],
    inner: Vec<(String, Arc<Expr>)>,
}

impl<'a> ElabScope<'a> {
    fn new(outer: &'a [(String, Expr)]) -> Self {
        Self {
            outer,
            inner: Vec::new(),
        }
    }

    fn push(&mut self, name: String, ty: Arc<Expr>) {
        self.inner.push((name, ty));
    }

    fn pop(&mut self) {
        self.inner.pop();
    }

    fn lookup(&self, name: &str) -> Option<Arc<Expr>> {
        if let Some((_, ty)) = self.inner.iter().rev().find(|(n, _)| n == name) {
            return Some(Arc::clone(ty));
        }
        self.outer
            .iter()
            .rev()
            .find(|(n, _)| n == name)
            .map(|(_, ty)| Arc::new(ty.clone()))
    }
}

/// Infer the type of `expr` under `env`, `local_context`, and `snapshot`.
///
/// Unlike `kernel::inference::infer`, unassigned `Expr::MVar(id)` nodes succeed by
/// looking up `id`'s declared statement in `snapshot.goals`.
pub fn infer(
    expr: &Expr,
    env: &Environment,
    local_context: &[(String, Expr)],
    snapshot: &Snapshot,
) -> Result<Expr, KernelError> {
    let inst = instantiate_mvars_arc(&Arc::new(expr.clone()), snapshot)?;
    let mut scope = ElabScope::new(local_context);
    let ty = infer_arc(&inst, env, &mut scope, snapshot)?;
    let ty_inst = instantiate_mvars_arc(&ty, snapshot)?;
    Ok(Arc::try_unwrap(ty_inst).unwrap_or_else(|a| (*a).clone()))
}

fn infer_arc(
    expr: &Arc<Expr>,
    env: &Environment,
    scope: &mut ElabScope<'_>,
    snapshot: &Snapshot,
) -> Result<Arc<Expr>, KernelError> {
    match &**expr {
        Expr::Sort(s) => {
            let next_level = UnivLevel::succ(Arc::new(s.level.clone()));
            Ok(Arc::new(Expr::sort(next_level)))
        }
        Expr::BVar(b) => Err(KernelError::UnboundBVar {
            idx: b.idx,
            context_len: scope.outer.len() + scope.inner.len(),
        }),
        Expr::MVar(m) => {
            let goal = snapshot
                .goals
                .get(&m.id)
                .ok_or_else(|| KernelError::InvalidValue {
                    message: format!("Unknown goal/metavariable '?{}'", m.id),
                    expr: Some((**expr).clone()),
                })?;
            if let Some(assigned) = &goal.assignment {
                let inst = instantiate_mvars_arc(&Arc::new(assigned.clone()), snapshot)?;
                return infer_arc(&inst, env, scope, snapshot);
            }
            instantiate_mvars_arc(&Arc::new(goal.statement.clone()), snapshot)
        }
        Expr::FVar(v) => {
            let ty = scope
                .lookup(&v.name)
                .ok_or_else(|| KernelError::UnknownFVar {
                    name: v.name.clone(),
                })?;
            instantiate_mvars_arc(&ty, snapshot)
        }
        Expr::Const(c) => {
            let decl = env
                .get(&c.name)
                .ok_or_else(|| KernelError::UnknownConstant {
                    name: c.name.clone(),
                })?;
            let (decl_ty, level_params) = match decl {
                Declaration::Definition(d) => (&d.ty, &d.level_params),
                Declaration::Axiom(d) => (&d.ty, &d.level_params),
                Declaration::Inductive(d) => (&d.ty, &d.level_params),
                Declaration::Constructor(d) => (&d.ty, &d.level_params),
                Declaration::Recursor(d) => (&d.ty, &d.level_params),
            };
            if level_params.len() != c.levels.len() {
                return Err(KernelError::InvalidUniverseArity {
                    name: c.name.clone(),
                    expected: level_params.len(),
                    actual: c.levels.len(),
                });
            }
            let inst_ty = instantiate_univ_level(decl_ty, level_params, &c.levels);
            Ok(Arc::new(inst_ty))
        }
        Expr::App(app) => {
            let fn_ty = infer_arc(&app.f, env, scope, snapshot)?;
            let fn_ty_whnf = whnf_arc(&fn_ty, env, snapshot)?;
            let Expr::Pi(pi) = &*fn_ty_whnf else {
                return Err(KernelError::NotAPi {
                    expr: (*app.f).clone(),
                    inferred_type: (*fn_ty_whnf).clone(),
                });
            };
            let arg_ty = infer_arc(&app.arg, env, scope, snapshot)?;
            let arg_ty_inst = instantiate_mvars_arc(&arg_ty, snapshot)?;
            let dom_inst = instantiate_mvars_arc(&pi.t, snapshot)?;
            if !is_def_eq_arc(Arc::clone(&arg_ty_inst), Arc::clone(&dom_inst), env) {
                return Err(KernelError::TypeMismatch {
                    expected: (*dom_inst).clone(),
                    actual: (*arg_ty_inst).clone(),
                    context_expr: Some((*app.arg).clone()),
                });
            }
            Ok(Arc::new(instantiate_bvar(&pi.body, &app.arg)))
        }
        Expr::Lam(lam) => {
            let dom_ty = infer_arc(&lam.t, env, scope, snapshot)?;
            let dom_ty_whnf = whnf_arc(&dom_ty, env, snapshot)?;
            let Expr::Sort(_) = &*dom_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*lam.t).clone(),
                    inferred_type: (*dom_ty_whnf).clone(),
                });
            };
            let fvar_name = format!("#elab.{}", uuid::Uuid::new_v4());
            let fvar = Expr::fvar(fvar_name.clone());
            scope.push(fvar_name.clone(), Arc::clone(&lam.t));
            let opened_body = Arc::new(instantiate_bvar(&lam.body, &fvar));
            let body_ty = infer_arc(&opened_body, env, scope, snapshot);
            scope.pop();
            let body_ty = body_ty?;
            let abstract_body_ty = Arc::new(bind(&body_ty, &fvar_name));
            Ok(Arc::new(Expr::pi(
                lam.var.clone(),
                Arc::clone(&lam.t),
                abstract_body_ty,
            )))
        }
        Expr::Pi(pi) => {
            let dom_ty = infer_arc(&pi.t, env, scope, snapshot)?;
            let dom_ty_whnf = whnf_arc(&dom_ty, env, snapshot)?;
            let Expr::Sort(u_sort) = &*dom_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*pi.t).clone(),
                    inferred_type: (*dom_ty_whnf).clone(),
                });
            };
            let fvar_name = format!("#elab.{}", uuid::Uuid::new_v4());
            let fvar = Expr::fvar(fvar_name.clone());
            scope.push(fvar_name, Arc::clone(&pi.t));
            let opened_body = Arc::new(instantiate_bvar(&pi.body, &fvar));
            let codom_ty = infer_arc(&opened_body, env, scope, snapshot);
            scope.pop();
            let codom_ty = codom_ty?;
            let codom_ty_whnf = whnf_arc(&codom_ty, env, snapshot)?;
            let Expr::Sort(v_sort) = &*codom_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*opened_body).clone(),
                    inferred_type: (*codom_ty_whnf).clone(),
                });
            };
            let imax_level = UnivLevel::imax(
                Arc::new(u_sort.level.clone()),
                Arc::new(v_sort.level.clone()),
            );
            Ok(Arc::new(Expr::sort(imax_level)))
        }
        Expr::Let(let_expr) => {
            let decl_ty = infer_arc(&let_expr.t, env, scope, snapshot)?;
            let decl_ty_whnf = whnf_arc(&decl_ty, env, snapshot)?;
            let Expr::Sort(_) = &*decl_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*let_expr.t).clone(),
                    inferred_type: (*decl_ty_whnf).clone(),
                });
            };
            let val_ty = infer_arc(&let_expr.value, env, scope, snapshot)?;
            let val_ty_inst = instantiate_mvars_arc(&val_ty, snapshot)?;
            let decl_ty_inst = instantiate_mvars_arc(&let_expr.t, snapshot)?;
            if !is_def_eq_arc(Arc::clone(&val_ty_inst), Arc::clone(&decl_ty_inst), env) {
                return Err(KernelError::TypeMismatch {
                    expected: (*decl_ty_inst).clone(),
                    actual: (*val_ty_inst).clone(),
                    context_expr: Some((*let_expr.value).clone()),
                });
            }
            let body_inst = Arc::new(instantiate_bvar(&let_expr.body, &let_expr.value));
            infer_arc(&body_inst, env, scope, snapshot)
        }
        Expr::Lit(lit) => match &lit.lit {
            Literal::Nat(_) => Ok(Arc::new(Expr::const_("Nat", vec![]))),
            Literal::Float(_) => Ok(Arc::new(Expr::const_("Float", vec![]))),
            Literal::String(_) => Ok(Arc::new(Expr::const_("String", vec![]))),
            Literal::Array(items) => {
                let (first, rest) = items.split_first().ok_or_else(|| {
                    KernelError::InvalidValue {
                        message: "Cannot infer element type of empty array literal".to_string(),
                        expr: Some((**expr).clone()),
                    }
                })?;
                let elem_ty = infer_arc(&Arc::new(first.clone()), env, scope, snapshot)?;
                for item in rest {
                    let item_ty = infer_arc(&Arc::new(item.clone()), env, scope, snapshot)?;
                    if !is_def_eq_arc(Arc::clone(&item_ty), Arc::clone(&elem_ty), env) {
                        return Err(KernelError::TypeMismatch {
                            expected: (*elem_ty).clone(),
                            actual: (*item_ty).clone(),
                            context_expr: Some(item.clone()),
                        });
                    }
                }
                let array_const = Arc::new(Expr::const_("Array", vec![]));
                Ok(Arc::new(Expr::app(array_const, elem_ty)))
            }
        },
    }
}
