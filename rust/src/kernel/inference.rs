//! Type inference for expressions in the poussins kernel.
//!
//! Internal kernel module decoupled from `state::Goal` and Python/PyO3 boundaries:
//! - `Sort(u)`          ==> `Sort(succ(u))`
//! - `FVar(x)`          ==> lookup `x` in local context (inner binders first, then outer hypotheses)
//! - `Const(c, ls)`     ==> declaration type with universe level instantiation (`instantiate_univ_level`)
//! - `App(f, a)`        ==> WHNF-reduce `infer(f)` to `Pi(_, dom, body)`, check `infer(a) ≡ dom`,
//!                          return `instantiate_bvar(body, a)`
//! - `Lam(x, t, b)`     ==> verify `infer(t)` reduces to `Sort`, open `b` with `x : t`,
//!                          infer `body_ty`, return `Pi(x, t, bind(body_ty, x))`
//! - `Pi(x, t, b)`      ==> reduce `infer(t)` to `Sort(u)`, open `b` with `x : t`,
//!                          reduce `infer(b)` to `Sort(v)`, return `Sort(imax(u, v))`
//! - `Let(x, t, v, b)`  ==> verify `infer(t)` reduces to `Sort` and `infer(v) ≡ t`,
//!                          substitute `v` and infer `b`
//! - `Lit(...)`         ==> `Nat`, `Float`, `String`, or homogeneous `Array T`
//!
//! Stage 2 / Stage 3 TODOs:
//! - [Metavariables] Resolve `Expr::MVar(id)` types via metavariable / session context.
//! - [Let-bound FVars] Support `let`-bound definitions in local context with context-aware WHNF unfolding.
//! - [Binder opening] Evaluate replacing `Uuid::new_v4()` in `fresh_infer_fvar_name` with a monotonic
//!   counter (`AtomicU64`) on hot paths.
//! - [Stack safety] Guard deep recursion with `stacker` or an explicit depth limit for PyO3 calls.

use std::sync::Arc;
use uuid::Uuid;

use crate::ast::expr::{Expr, Literal};
use crate::ast::ops::{bind, instantiate_bvar, instantiate_univ_level};
use crate::ast::univ_level::UnivLevel;
use crate::environment::declaration::Declaration;
use crate::environment::environment::Environment;
use crate::error::KernelError;
use crate::kernel::equality::is_def_eq_arc;
use crate::kernel::reduction::whnf_arc;

// ---------------------------------------------------------------------------
// Internal Local Scope (decoupled from `state::Goal`)
// ---------------------------------------------------------------------------

/// Lightweight scope combining caller-supplied hypotheses (e.g. `&goal.local_context`
/// or `&[]` at top-level) with inner binder variables opened during inference.
pub(crate) struct InferScope<'a> {
    outer: &'a [(String, Expr)],
    inner: Vec<(String, Arc<Expr>)>,
}

impl<'a> InferScope<'a> {
    pub(crate) fn new(outer: &'a [(String, Expr)]) -> Self {
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

    /// Look up the most recent binding for `name` (inner binders shadow outer hypotheses,
    /// and later entries shadow earlier entries, matching `Goal::lookup_local`).
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

// ---------------------------------------------------------------------------
// Entry Point
// ---------------------------------------------------------------------------

/// Infer the type of `expr` under `env` and an ordered slice of local hypotheses `local_context`.
pub(crate) fn infer(
    expr: &Expr,
    env: &Environment,
    local_context: &[(String, Expr)],
) -> Result<Expr, KernelError> {
    let mut scope = InferScope::new(local_context);
    let arc_ty = infer_arc(&Arc::new(expr.clone()), env, &mut scope)?;
    Ok(Arc::try_unwrap(arc_ty).unwrap_or_else(|a| (*a).clone()))
}

// ---------------------------------------------------------------------------
// Core Type Inference Engine
// ---------------------------------------------------------------------------

/// Create a collision-free fresh free variable name for opening binders during inference.
#[inline]
fn fresh_infer_fvar_name() -> String {
    format!("#infer.{}", Uuid::new_v4())
}

/// Infer the type of an `Arc<Expr>` node.
pub(crate) fn infer_arc(
    expr: &Arc<Expr>,
    env: &Environment,
    scope: &mut InferScope<'_>,
) -> Result<Arc<Expr>, KernelError> {
    match &**expr {
        Expr::Sort(s) => {
            let next_level = UnivLevel::succ(Arc::new(s.level.clone()));
            Ok(Arc::new(Expr::sort(next_level)))
        }
        Expr::BVar(b) => Err(KernelError::UnboundBVar {
            idx: b.idx,
            context_len: 0,
        }),
        Expr::MVar(m) => Err(KernelError::InvalidValue {
            message: format!(
                "Cannot infer type of metavariable '?{}' without a metavariable context",
                m.id
            ),
            expr: Some((**expr).clone()),
        }),
        Expr::FVar(v) => scope
            .lookup(&v.name)
            .ok_or_else(|| KernelError::UnknownFVar {
                name: v.name.clone(),
            }),
        Expr::Const(c) => infer_const(&c.name, &c.levels, env),
        Expr::App(app) => {
            let fn_ty = infer_arc(&app.f, env, scope)?;
            let fn_ty_whnf = whnf_arc(fn_ty, env);
            let Expr::Pi(pi) = &*fn_ty_whnf else {
                return Err(KernelError::NotAPi {
                    expr: (*app.f).clone(),
                    inferred_type: (*fn_ty_whnf).clone(),
                });
            };
            let arg_ty = infer_arc(&app.arg, env, scope)?;
            if !is_def_eq_arc(Arc::clone(&arg_ty), Arc::clone(&pi.t), env) {
                return Err(KernelError::TypeMismatch {
                    expected: (*pi.t).clone(),
                    actual: (*arg_ty).clone(),
                    context_expr: Some((*app.arg).clone()),
                });
            }
            Ok(Arc::new(instantiate_bvar(&pi.body, &app.arg)))
        }
        Expr::Lam(lam) => {
            // 1. Domain `lam.t` must be a well-formed type (reduces in WHNF to a `Sort`).
            let dom_ty = infer_arc(&lam.t, env, scope)?;
            let dom_ty_whnf = whnf_arc(dom_ty, env);
            let Expr::Sort(_) = &*dom_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*lam.t).clone(),
                    inferred_type: (*dom_ty_whnf).clone(),
                });
            };

            // 2. Open the body with a fresh FVar `x : lam.t` and infer its type.
            let fvar_name = fresh_infer_fvar_name();
            let fvar = Expr::fvar(fvar_name.clone());
            scope.push(fvar_name.clone(), Arc::clone(&lam.t));
            let opened_body = Arc::new(instantiate_bvar(&lam.body, &fvar));
            let body_ty = infer_arc(&opened_body, env, scope);
            scope.pop();
            let body_ty = body_ty?;

            // 3. Re-abstract `fvar` back to `BVar(0)` to form `Pi(var, lam.t, body_ty)`.
            let abstract_body_ty = Arc::new(bind(&body_ty, &fvar_name));
            Ok(Arc::new(Expr::pi(
                lam.var.clone(),
                Arc::clone(&lam.t),
                abstract_body_ty,
            )))
        }
        Expr::Pi(pi) => {
            // 1. Domain `pi.t : Sort(u)`
            let dom_ty = infer_arc(&pi.t, env, scope)?;
            let dom_ty_whnf = whnf_arc(dom_ty, env);
            let Expr::Sort(u_sort) = &*dom_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*pi.t).clone(),
                    inferred_type: (*dom_ty_whnf).clone(),
                });
            };

            // 2. Codomain `pi.body[x] : Sort(v)` under `x : pi.t`
            let fvar_name = fresh_infer_fvar_name();
            let fvar = Expr::fvar(fvar_name.clone());
            scope.push(fvar_name, Arc::clone(&pi.t));
            let opened_body = Arc::new(instantiate_bvar(&pi.body, &fvar));
            let codom_ty = infer_arc(&opened_body, env, scope);
            scope.pop();
            let codom_ty = codom_ty?;
            let codom_ty_whnf = whnf_arc(codom_ty, env);
            let Expr::Sort(v_sort) = &*codom_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*opened_body).clone(),
                    inferred_type: (*codom_ty_whnf).clone(),
                });
            };

            // 3. Impredicative product universe `Sort(imax(u, v))`
            let imax_level = UnivLevel::imax(
                Arc::new(u_sort.level.clone()),
                Arc::new(v_sort.level.clone()),
            );
            Ok(Arc::new(Expr::sort(imax_level)))
        }
        Expr::Let(let_expr) => {
            // 1. Declared type `let_expr.t` must be a valid `Sort`.
            let decl_ty = infer_arc(&let_expr.t, env, scope)?;
            let decl_ty_whnf = whnf_arc(decl_ty, env);
            let Expr::Sort(_) = &*decl_ty_whnf else {
                return Err(KernelError::NotASort {
                    expr: (*let_expr.t).clone(),
                    inferred_type: (*decl_ty_whnf).clone(),
                });
            };

            // 2. Value must match the declared type `let_expr.t`.
            let val_ty = infer_arc(&let_expr.value, env, scope)?;
            if !is_def_eq_arc(Arc::clone(&val_ty), Arc::clone(&let_expr.t), env) {
                return Err(KernelError::TypeMismatch {
                    expected: (*let_expr.t).clone(),
                    actual: (*val_ty).clone(),
                    context_expr: Some((*let_expr.value).clone()),
                });
            }

            // 3. Substitute `value` into `body` (zeta-style) and infer its type.
            let body_inst = Arc::new(instantiate_bvar(&let_expr.body, &let_expr.value));
            infer_arc(&body_inst, env, scope)
        }
        Expr::Lit(lit) => infer_literal(&lit.lit, expr, env, scope),
    }
}

// ---------------------------------------------------------------------------
// Helpers: Constant Lookup & Literals
// ---------------------------------------------------------------------------

/// Look up a constant in `env` and instantiate its universe level parameters.
fn infer_const(
    name: &str,
    levels: &[UnivLevel],
    env: &Environment,
) -> Result<Arc<Expr>, KernelError> {
    let decl = env
        .get(name)
        .ok_or_else(|| KernelError::UnknownConstant {
            name: name.to_string(),
        })?;
    let (decl_ty, level_params) = match decl {
        Declaration::Definition(d) => (&d.ty, &d.level_params),
        Declaration::Axiom(d) => (&d.ty, &d.level_params),
        Declaration::Inductive(d) => (&d.ty, &d.level_params),
        Declaration::Constructor(d) => (&d.ty, &d.level_params),
        Declaration::Recursor(d) => (&d.ty, &d.level_params),
    };
    if level_params.len() != levels.len() {
        return Err(KernelError::InvalidUniverseArity {
            name: name.to_string(),
            expected: level_params.len(),
            actual: levels.len(),
        });
    }
    let inst_ty = instantiate_univ_level(decl_ty, level_params, levels);
    Ok(Arc::new(inst_ty))
}

/// Infer the type of a literal expression.
fn infer_literal(
    lit: &Literal,
    expr: &Arc<Expr>,
    env: &Environment,
    scope: &mut InferScope<'_>,
) -> Result<Arc<Expr>, KernelError> {
    match lit {
        Literal::Nat(_) => Ok(Arc::new(Expr::const_("Nat", vec![]))),
        Literal::Float(_) => Ok(Arc::new(Expr::const_("Float", vec![]))),
        Literal::String(_) => Ok(Arc::new(Expr::const_("String", vec![]))),
        Literal::Array(items) => {
            let (first, rest) = items.split_first().ok_or_else(|| KernelError::InvalidValue {
                message: "Cannot infer element type of empty array literal".to_string(),
                expr: Some((**expr).clone()),
            })?;
            let elem_ty = infer_arc(&Arc::new(first.clone()), env, scope)?;
            for item in rest {
                let item_ty = infer_arc(&Arc::new(item.clone()), env, scope)?;
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
    }
}
