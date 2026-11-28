//! Unification engine for metavariables / goals in the poussins elaborator.
//!
//! Operates on a mutable `Snapshot` (where open and assigned goals are unified
//! in `Snapshot::goals`), solving equations between expressions modulo `instantiate_mvars`
//! and WHNF reduction while enforcing scope and occurs checks.

use std::collections::HashSet;
use std::sync::Arc;

use crate::ast::expr::{Expr, Literal};
use crate::ast::ops::{collect_fvar_names, instantiate_bvar};
use crate::elaborator::calc::{instantiate_mvars_arc, whnf_arc};
use crate::environment::environment::Environment;
use crate::error::KernelError;
use crate::kernel::equality::is_def_eq_univ_level;
use crate::state::snapshot::Snapshot;

/// Unify two expressions `lhs` and `rhs` under `env`, mutating `snapshot.goals`
/// with any newly solved goal assignments.
///
/// Returns `Ok(true)` if unification succeeded, `Ok(false)` if the expressions
/// cannot be unified, or `Err(KernelError)` on invalid/cyclic goal state.
pub fn unify(
    lhs: &Expr,
    rhs: &Expr,
    env: &Environment,
    snapshot: &mut Snapshot,
) -> Result<bool, KernelError> {
    unify_arc(
        &Arc::new(lhs.clone()),
        &Arc::new(rhs.clone()),
        env,
        snapshot,
    )
}

pub(crate) fn unify_arc(
    lhs: &Arc<Expr>,
    rhs: &Arc<Expr>,
    env: &Environment,
    snapshot: &mut Snapshot,
) -> Result<bool, KernelError> {
    let lhs_inst = instantiate_mvars_arc(lhs, snapshot)?;
    let rhs_inst = instantiate_mvars_arc(rhs, snapshot)?;

    if Arc::ptr_eq(&lhs_inst, &rhs_inst) || *lhs_inst == *rhs_inst {
        return Ok(true);
    }

    match (&*lhs_inst, &*rhs_inst) {
        (Expr::MVar(m1), Expr::MVar(m2)) if m1.id == m2.id => return Ok(true),
        (Expr::MVar(m), other) => {
            return assign_goal(&m.id, other, env, snapshot);
        }
        (other, Expr::MVar(m)) => {
            return assign_goal(&m.id, other, env, snapshot);
        }
        _ => {}
    }

    let lhs_whnf = whnf_arc(&lhs_inst, env, snapshot)?;
    let rhs_whnf = whnf_arc(&rhs_inst, env, snapshot)?;

    if Arc::ptr_eq(&lhs_whnf, &rhs_whnf) || *lhs_whnf == *rhs_whnf {
        return Ok(true);
    }

    match (&*lhs_whnf, &*rhs_whnf) {
        (Expr::MVar(m1), Expr::MVar(m2)) if m1.id == m2.id => Ok(true),
        (Expr::MVar(m), other) => assign_goal(&m.id, other, env, snapshot),
        (other, Expr::MVar(m)) => assign_goal(&m.id, other, env, snapshot),

        (Expr::Sort(s1), Expr::Sort(s2)) => Ok(is_def_eq_univ_level(&s1.level, &s2.level)),
        (Expr::FVar(v1), Expr::FVar(v2)) => Ok(v1.name == v2.name),
        (Expr::BVar(b1), Expr::BVar(b2)) => Ok(b1.idx == b2.idx),

        (Expr::Const(c1), Expr::Const(c2)) => {
            if c1.name != c2.name || c1.levels.len() != c2.levels.len() {
                return Ok(false);
            }
            Ok(c1
                .levels
                .iter()
                .zip(c2.levels.iter())
                .all(|(l1, l2)| is_def_eq_univ_level(l1, l2)))
        }

        (Expr::Lit(l1), Expr::Lit(l2)) => unify_literal(&l1.lit, &l2.lit, env, snapshot),

        (Expr::App(a1), Expr::App(a2)) => {
            if !unify_arc(&a1.f, &a2.f, env, snapshot)? {
                return Ok(false);
            }
            unify_arc(&a1.arg, &a2.arg, env, snapshot)
        }

        (Expr::Lam(l1), Expr::Lam(l2)) => {
            if !unify_arc(&l1.t, &l2.t, env, snapshot)? {
                return Ok(false);
            }
            let fresh = Expr::fvar(format!("#unif.{}", uuid::Uuid::new_v4()));
            let b1 = Arc::new(instantiate_bvar(&l1.body, &fresh));
            let b2 = Arc::new(instantiate_bvar(&l2.body, &fresh));
            unify_arc(&b1, &b2, env, snapshot)
        }

        (Expr::Pi(p1), Expr::Pi(p2)) => {
            if !unify_arc(&p1.t, &p2.t, env, snapshot)? {
                return Ok(false);
            }
            let fresh = Expr::fvar(format!("#unif.{}", uuid::Uuid::new_v4()));
            let b1 = Arc::new(instantiate_bvar(&p1.body, &fresh));
            let b2 = Arc::new(instantiate_bvar(&p2.body, &fresh));
            unify_arc(&b1, &b2, env, snapshot)
        }

        (Expr::Let(l1), Expr::Let(l2)) => {
            if !unify_arc(&l1.t, &l2.t, env, snapshot)?
                || !unify_arc(&l1.value, &l2.value, env, snapshot)?
            {
                return Ok(false);
            }
            let fresh = Expr::fvar(format!("#unif.{}", uuid::Uuid::new_v4()));
            let b1 = Arc::new(instantiate_bvar(&l1.body, &fresh));
            let b2 = Arc::new(instantiate_bvar(&l2.body, &fresh));
            unify_arc(&b1, &b2, env, snapshot)
        }

        _ => Ok(false),
    }
}

fn unify_literal(
    l1: &Literal,
    l2: &Literal,
    env: &Environment,
    snapshot: &mut Snapshot,
) -> Result<bool, KernelError> {
    match (l1, l2) {
        (Literal::Nat(a), Literal::Nat(b)) => Ok(a == b),
        (Literal::Float(a), Literal::Float(b)) => Ok(a.to_bits() == b.to_bits()),
        (Literal::String(a), Literal::String(b)) => Ok(a == b),
        (Literal::Array(a), Literal::Array(b)) => {
            if a.len() != b.len() {
                return Ok(false);
            }
            for (ea, eb) in a.iter().zip(b.iter()) {
                if !unify_arc(&Arc::new(ea.clone()), &Arc::new(eb.clone()), env, snapshot)? {
                    return Ok(false);
                }
            }
            Ok(true)
        }
        _ => Ok(false),
    }
}

/// Attempt to assign `rhs` to open goal `goal_id` after scope and occurs checks.
fn assign_goal(
    goal_id: &str,
    rhs: &Expr,
    env: &Environment,
    snapshot: &mut Snapshot,
) -> Result<bool, KernelError> {
    let rhs_inst = Arc::try_unwrap(instantiate_mvars_arc(&Arc::new(rhs.clone()), snapshot)?)
        .unwrap_or_else(|a| (*a).clone());

    let Some(goal) = snapshot.goals.get(goal_id).cloned() else {
        return Err(KernelError::InvalidValue {
            message: format!("Unknown goal '?{goal_id}' during unification"),
            expr: Some(rhs_inst),
        });
    };

    if let Some(existing) = &goal.assignment {
        return unify_arc(
            &Arc::new(existing.clone()),
            &Arc::new(rhs_inst),
            env,
            snapshot,
        );
    }

    if occurs_in_goal(goal_id, &rhs_inst, snapshot)? {
        return Ok(false);
    }

    if !collect_fvar_names(&rhs_inst)
        .iter()
        .all(|name| goal.has_local_hypothesis(name))
    {
        return Ok(false);
    }

    snapshot.assign(goal_id, rhs_inst);
    Ok(true)
}

/// Return `true` if `target_goal_id` occurs in `expr` (transitively unfolding assigned goals).
fn occurs_in_goal(
    target_goal_id: &str,
    expr: &Expr,
    snapshot: &Snapshot,
) -> Result<bool, KernelError> {
    let mut visited = HashSet::new();
    occurs_inner(target_goal_id, expr, snapshot, &mut visited)
}

fn occurs_inner(
    target_goal_id: &str,
    expr: &Expr,
    snapshot: &Snapshot,
    visited: &mut HashSet<String>,
) -> Result<bool, KernelError> {
    match expr {
        Expr::BVar(_) | Expr::FVar(_) | Expr::Sort(_) | Expr::Const(_) => Ok(false),
        Expr::MVar(m) => {
            if m.id == target_goal_id {
                return Ok(true);
            }
            if let Some(goal) = snapshot.goals.get(&m.id) {
                if let Some(assigned) = &goal.assignment {
                    if !visited.insert(m.id.clone()) {
                        return Err(KernelError::InvalidValue {
                            message: format!("Cyclic goal assignment detected for '?{}'", m.id),
                            expr: Some(expr.clone()),
                        });
                    }
                    let found = occurs_inner(target_goal_id, assigned, snapshot, visited);
                    visited.remove(&m.id);
                    return found;
                }
            }
            Ok(false)
        }
        Expr::App(app) => Ok(occurs_inner(target_goal_id, &app.f, snapshot, visited)?
            || occurs_inner(target_goal_id, &app.arg, snapshot, visited)?),
        Expr::Lam(lam) => Ok(occurs_inner(target_goal_id, &lam.t, snapshot, visited)?
            || occurs_inner(target_goal_id, &lam.body, snapshot, visited)?),
        Expr::Pi(pi) => Ok(occurs_inner(target_goal_id, &pi.t, snapshot, visited)?
            || occurs_inner(target_goal_id, &pi.body, snapshot, visited)?),
        Expr::Let(let_expr) => Ok(occurs_inner(target_goal_id, &let_expr.t, snapshot, visited)?
            || occurs_inner(target_goal_id, &let_expr.value, snapshot, visited)?
            || occurs_inner(target_goal_id, &let_expr.body, snapshot, visited)?),
        Expr::Lit(lit) => match &lit.lit {
            Literal::Nat(_) | Literal::Float(_) | Literal::String(_) => Ok(false),
            Literal::Array(items) => {
                for item in items {
                    if occurs_inner(target_goal_id, item, snapshot, visited)? {
                        return Ok(true);
                    }
                }
                Ok(false)
            }
        },
    }
}
