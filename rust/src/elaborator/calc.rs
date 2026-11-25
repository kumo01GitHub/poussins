//! Metavariable-aware calculation utilities for the poussins elaborator.
//!
//! Bridges `state` (metavariable assignments) and `kernel` (pure reduction,
//! type inference, and definitional equality):
//! - `instantiate_univ_mvars` / `instantiate_mvars`: transitively unfold assigned
//!   universe and expression metavariables with cycle protection and Arc sharing.
//! - `whnf_mvar` / `whnf_mvar_arc`: instantiate metavariables at the head and reduce
//!   to Weak Head Normal Form via `kernel::reduction::whnf_arc`.
//! - `infer_mvar` / `infer_mvar_arc`: infer the type of expressions containing
//!   unassigned metavariables by consulting `MetaContext` and `kernel::inference`.
//! - `is_def_eq_mvar`: check definitional equality after metavariable instantiation.

use std::collections::HashSet;
use std::sync::Arc;

use crate::ast::expr::{Expr, Literal};
use crate::ast::ops::{bind, instantiate_bvar, instantiate_univ_level};
use crate::ast::univ_level::UnivLevel;
use crate::core::error::KernelError;
use crate::environment::declaration::Declaration;
use crate::environment::environment::Environment;
use crate::kernel::equality::is_def_eq_arc;
use crate::kernel::reduction::whnf_arc;

// ---------------------------------------------------------------------------
// Metavariable Context Abstraction (decoupled from concrete `Snapshot` layout)
// ---------------------------------------------------------------------------

/// Read-only view of metavariable assignments and declarations needed during
/// elaboration calculations. Implemented by `state::Snapshot`.
pub(crate) trait MetaContext {
    /// Look up the assigned expression for metavariable `id`, if solved.
    fn get_mvar_assignment(&self, id: &str) -> Option<&Expr>;

    /// Look up the declared type of metavariable `id`.
    fn get_mvar_type(&self, id: &str) -> Option<&Expr>;

    /// Look up the assigned universe level for universe metavariable `id`, if solved.
    fn get_univ_mvar_assignment(&self, _id: &str) -> Option<&UnivLevel> {
        None
    }
}

// ---------------------------------------------------------------------------
// Transitive Metavariable Instantiation
// ---------------------------------------------------------------------------

/// Transitively instantiate all solved universe metavariables inside `level`.
pub(crate) fn instantiate_univ_mvars<C: MetaContext>(
    level: &UnivLevel,
    ctx: &C,
) -> Result<UnivLevel, KernelError> {
    let mut visited = HashSet::new();
    instantiate_univ_mvars_inner(level, ctx, &mut visited)
}

fn instantiate_univ_mvars_inner<C: MetaContext>(
    level: &UnivLevel,
    ctx: &C,
    visited: &mut HashSet<String>,
) -> Result<UnivLevel, KernelError> {
    match level {
        UnivLevel::Zero(_) => Ok(level.clone()),
        UnivLevel::Param(p) => {
            if let Some(assigned) = ctx.get_univ_mvar_assignment(&p.name) {
                if !visited.insert(p.name.clone()) {
                    return Err(KernelError::InvalidValue {
                        message: format!(
                            "Cyclic universe metavariable assignment detected for '?{}'",
                            p.name
                        ),
                        expr: None,
                    });
                }
                let res = instantiate_univ_mvars_inner(assigned, ctx, visited);
                visited.remove(&p.name);
                res
            } else {
                Ok(level.clone())
            }
        }
        UnivLevel::Succ(s) => {
            let pred = instantiate_univ_mvars_inner(&s.pred, ctx, visited)?;
            if pred == *s.pred {
                Ok(level.clone())
            } else {
                Ok(UnivLevel::succ(Arc::new(pred)))
            }
        }
        UnivLevel::Max(m) => {
            let left = instantiate_univ_mvars_inner(&m.left, ctx, visited)?;
            let right = instantiate_univ_mvars_inner(&m.right, ctx, visited)?;
            if left == *m.left && right == *m.right {
                Ok(level.clone())
            } else {
                Ok(UnivLevel::max(Arc::new(left), Arc::new(right)))
            }
        }
        UnivLevel::IMax(im) => {
            let left = instantiate_univ_mvars_inner(&im.left, ctx, visited)?;
            let right = instantiate_univ_mvars_inner(&im.right, ctx, visited)?;
            if left == *im.left && right == *im.right {
                Ok(level.clone())
            } else {
                Ok(UnivLevel::imax(Arc::new(left), Arc::new(right)))
            }
        }
    }
}

/// Transitively instantiate all solved expression and universe metavariables in `expr`.
///
/// Reuses existing `Arc` nodes whenever subtrees contain no solved metavariables.
pub(crate) fn instantiate_mvars<C: MetaContext>(
    expr: &Expr,
    ctx: &C,
) -> Result<Expr, KernelError> {
    let arc_res = instantiate_mvars_arc(&Arc::new(expr.clone()), ctx)?;
    Ok(Arc::try_unwrap(arc_res).unwrap_or_else(|a| (*a).clone()))
}

/// `Arc<Expr>` version of `instantiate_mvars` preserving pointer identity when unchanged.
pub(crate) fn instantiate_mvars_arc<C: MetaContext>(
    expr: &Arc<Expr>,
    ctx: &C,
) -> Result<Arc<Expr>, KernelError> {
    let mut visited = HashSet::new();
    instantiate_mvars_inner(expr, ctx, &mut visited)
}

fn instantiate_mvars_inner<C: MetaContext>(
    expr: &Arc<Expr>,
    ctx: &C,
    visited: &mut HashSet<String>,
) -> Result<Arc<Expr>, KernelError> {
    match &**expr {
        Expr::BVar(_) | Expr::FVar(_) => Ok(Arc::clone(expr)),

        Expr::MVar(m) => {
            if let Some(assigned) = ctx.get_mvar_assignment(&m.id) {
                if !visited.insert(m.id.clone()) {
                    return Err(KernelError::InvalidValue {
                        message: format!(
                            "Cyclic metavariable assignment detected for '?{}'",
                            m.id
                        ),
                        expr: Some((**expr).clone()),
                    });
                }
                let res = instantiate_mvars_inner(&Arc::new(assigned.clone()), ctx, visited);
                visited.remove(&m.id);
                res
            } else {
                Ok(Arc::clone(expr))
            }
        }

        Expr::Sort(s) => {
            let new_lvl = instantiate_univ_mvars(&s.level, ctx)?;
            if new_lvl == s.level {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::sort(new_lvl)))
            }
        }

        Expr::Const(c) => {
            if c.levels.is_empty() {
                return Ok(Arc::clone(expr));
            }
            let mut changed = false;
            let mut new_levels = Vec::with_capacity(c.levels.len());
            for lvl in &c.levels {
                let inst = instantiate_univ_mvars(lvl, ctx)?;
                if inst != *lvl {
                    changed = true;
                }
                new_levels.push(inst);
            }
            if changed {
                Ok(Arc::new(Expr::const_(c.name.clone(), new_levels)))
            } else {
                Ok(Arc::clone(expr))
            }
        }

        Expr::App(app) => {
            let f = instantiate_mvars_inner(&app.f, ctx, visited)?;
            let arg = instantiate_mvars_inner(&app.arg, ctx, visited)?;
            if Arc::ptr_eq(&app.f, &f) && Arc::ptr_eq(&app.arg, &arg) {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::app(f, arg)))
            }
        }

        Expr::Lam(lam) => {
            let t = instantiate_mvars_inner(&lam.t, ctx, visited)?;
            let body = instantiate_mvars_inner(&lam.body, ctx, visited)?;
            if Arc::ptr_eq(&lam.t, &t) && Arc::ptr_eq(&lam.body, &body) {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::lam(lam.var.clone(), t, body)))
            }
        }

        Expr::Pi(pi) => {
            let t = instantiate_mvars_inner(&pi.t, ctx, visited)?;
            let body = instantiate_mvars_inner(&pi.body, ctx, visited)?;
            if Arc::ptr_eq(&pi.t, &t) && Arc::ptr_eq(&pi.body, &body) {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::pi(pi.var.clone(), t, body)))
            }
        }

        Expr::Let(let_expr) => {
            let t = instantiate_mvars_inner(&let_expr.t, ctx, visited)?;
            let value = instantiate_mvars_inner(&let_expr.value, ctx, visited)?;
            let body = instantiate_mvars_inner(&let_expr.body, ctx, visited)?;
            if Arc::ptr_eq(&let_expr.t, &t)
                && Arc::ptr_eq(&let_expr.value, &value)
                && Arc::ptr_eq(&let_expr.body, &body)
            {
                Ok(Arc::clone(expr))
            } else {
                Ok(Arc::new(Expr::let_(let_expr.var.clone(), t, value, body)))
            }
        }

        Expr::Lit(lit) => match &lit.lit {
            Literal::Nat(_) | Literal::Float(_) | Literal::String(_) => Ok(Arc::clone(expr)),
            Literal::Array(items) => {
                let mut changed = false;
                let mut new_items = Vec::with_capacity(items.len());
                for item in items {
                    let item_arc = Arc::new(item.clone());
                    let inst = instantiate_mvars_inner(&item_arc, ctx, visited)?;
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
pub(crate) fn whnf_mvar<C: MetaContext>(
    expr: &Expr,
    env: &Environment,
    ctx: &C,
) -> Result<Expr, KernelError> {
    let arc_res = whnf_mvar_arc(&Arc::new(expr.clone()), env, ctx)?;
    Ok(Arc::try_unwrap(arc_res).unwrap_or_else(|a| (*a).clone()))
}

/// `Arc<Expr>` version of `whnf_mvar`.
pub(crate) fn whnf_mvar_arc<C: MetaContext>(
    expr: &Arc<Expr>,
    env: &Environment,
    ctx: &C,
) -> Result<Arc<Expr>, KernelError> {
    let inst = instantiate_mvars_arc(expr, ctx)?;
    Ok(whnf_arc(inst, env))
}

/// Check definitional equality of `t` and `s` after instantiating solved metavariables.
pub(crate) fn is_def_eq_mvar<C: MetaContext>(
    t: &Expr,
    s: &Expr,
    env: &Environment,
    ctx: &C,
) -> Result<bool, KernelError> {
    let t_inst = instantiate_mvars_arc(&Arc::new(t.clone()), ctx)?;
    let s_inst = instantiate_mvars_arc(&Arc::new(s.clone()), ctx)?;
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

/// Infer the type of `expr` under `env`, `local_context`, and metavariable context `ctx`.
///
/// Unlike `kernel::inference::infer`, unassigned `Expr::MVar(id)` nodes succeed by
/// looking up `id`'s declared type in `ctx` (and instantiating solved assignments in it).
pub(crate) fn infer_mvar<C: MetaContext>(
    expr: &Expr,
    env: &Environment,
    local_context: &[(String, Expr)],
    ctx: &C,
) -> Result<Expr, KernelError> {
    let inst = instantiate_mvars_arc(&Arc::new(expr.clone()), ctx)?;
    let mut scope = ElabScope::new(local_context);
    let ty = infer_mvar_arc(&inst, env, &mut scope, ctx)?;
    let ty_inst = instantiate_mvars_arc(&ty, ctx)?;
    Ok(Arc::try_unwrap(ty_inst).unwrap_or_else(|a| (*a).clone()))
}

fn infer_mvar_arc<C: MetaContext>(
    expr: &Arc<Expr>,
    env: &Environment,
    scope: &mut ElabScope<'_>,
    ctx: &C,
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
            if let Some(assigned) = ctx.get_mvar_assignment(&m.id) {
                let inst = instantiate_mvars_arc(&Arc::new(assigned.clone()), ctx)?;
                return infer_mvar_arc(&inst, env, scope, ctx);
            }
            let mvar_ty = ctx
                .get_mvar_type(&m.id)
                .ok_or_else(|| KernelError::InvalidValue {
                    message: format!("Unknown metavariable '?{}'", m.id),
                    expr: Some((**expr).clone()),
                })?;
            instantiate_mvars_arc(&Arc::new(mvar_ty.clone()), ctx)
        }
        Expr::FVar(v) => {
            let ty = scope
                .lookup(&v.name)
                .ok_or_else(|| KernelError::UnknownFVar {
                    name: v.name.clone(),
                })?;
            instantiate_mvars_arc(&ty, ctx)
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
            let fn_ty = infer_mvar_arc(&app.f, env, scope, ctx)?;
            let fn_ty_whnf = whnf_mvar_arc(&fn_ty, env, ctx)?;
            let Expr::Pi(pi) = &*fn_ty_whnf else {
                return Err(KernelError::NotAPi {
                    expr: (*app.f).clone(),
                    inferred_type: (*fn_ty_whnf).clone(),
                });
            };
            let arg_ty = infer_mvar_arc(&app.arg, env, scope, ctx)?;
            let arg_ty_inst = instantiate_mvars_arc(&arg_ty, ctx)?;
            let dom_inst = instantiate_mvars_arc(&pi.t, ctx)?;
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
            let dom_ty = infer_mvar_arc(&lam.t, env, scope, ctx)?;
            let dom_ty_whnf = whnf_mvar_arc(&dom_ty, env, ctx)?;
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
            let body_ty = infer_mvar_arc(&opened_body, env, scope, ctx);
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
            let dom_ty = infer_mvar_arc(&pi.t, env, scope, ctx)?;
            let dom_ty_whnf = whnf_mvar_arc(&dom_ty, env, ctx)?;
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
            let codom_ty = infer_mvar_arc(&opened_body, env, scope, ctx);
            scope.pop();
            let codom_ty = codom_ty?;
            let codom_ty_whnf = whnf_mvar_arc(&codom_ty, env, ctx)?;
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
            let decl_ty = infer_mvar_arc(&let_expr.t, env, scope, ctx)?;
            let decl_ty_whnf = whnf_mvar_arc(&decl_ty, env, ctx)?;
            let Expr::Sort(_) = &*decl_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*let_expr.t).clone(),
                    inferred_type: (*decl_ty_whnf).clone(),
                });
            };

            let val_ty = infer_mvar_arc(&let_expr.value, env, scope, ctx)?;
            let val_ty_inst = instantiate_mvars_arc(&val_ty, ctx)?;
            let decl_ty_inst = instantiate_mvars_arc(&let_expr.t, ctx)?;
            if !is_def_eq_arc(Arc::clone(&val_ty_inst), Arc::clone(&decl_ty_inst), env) {
                return Err(KernelError::TypeMismatch {
                    expected: (*decl_ty_inst).clone(),
                    actual: (*val_ty_inst).clone(),
                    context_expr: Some((*let_expr.value).clone()),
                });
            }

            let body_inst = Arc::new(instantiate_bvar(&let_expr.body, &let_expr.value));
            infer_mvar_arc(&body_inst, env, scope, ctx)
        }
        Expr::Lit(lit) => match &lit.lit {
            Literal::Nat(_) => Ok(Arc::new(Expr::const_("Nat", vec![]))),
            Literal::Float(_) => Ok(Arc::new(Expr::const_("Float", vec![]))),
            Literal::String(_) => Ok(Arc::new(Expr::const_("String", vec![]))),
            Literal::Array(items) => {
                let (first, rest) =
                    items
                        .split_first()
                        .ok_or_else(|| KernelError::InvalidValue {
                            message: "Cannot infer element type of empty array literal".to_string(),
                            expr: Some((**expr).clone()),
                        })?;
                let elem_ty = infer_mvar_arc(&Arc::new(first.clone()), env, scope, ctx)?;
                for item in rest {
                    let item_ty = infer_mvar_arc(&Arc::new(item.clone()), env, scope, ctx)?;
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
