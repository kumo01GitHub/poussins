//! Definitional equality for universe levels and expressions in the poussins kernel.
//!
//! Stage 1 (pure syntactic + WHNF + delta/iota equality):
//! - Universe level algebra (`is_level_def_eq`): `max`, `imax`, `succ` normalization & semilattice laws.
//! - Expression definitional equality (`is_def_eq`):
//!   1. Fast pointer / structural equality check.
//!   2. Weak Head Normal Form (WHNF) reduction via `whnf_arc` (beta, zeta, delta, iota).
//!   3. Structural head & binder comparison (`Sort`, `Const`, `FVar`, `BVar`, `Lit`, `MVar`, `App`, `Lam`, `Pi`, `Let`).
//!
//! Stage 2 hooks (to be added once `TypeChecker::infer` is in place):
//! - Proof irrelevance (`is_prop` check on inferred types).
//! - Eta-equivalence (`Lam` vs non-`Lam` when type reduces to `Pi`).
//! - Nat literal vs `Nat.zero` / `Nat.succ` unfolding.

use std::collections::BTreeSet;
use std::sync::Arc;

use uuid::Uuid;

use crate::ast::expr::{Expr, Literal};
use crate::ast::ops::instantiate_bvar;
use crate::ast::univ_level::UnivLevel;
use crate::environment::environment::Environment;
use crate::kernel::reduction::whnf_arc;

// ---------------------------------------------------------------------------
// Universe Level Definitional Equality
// ---------------------------------------------------------------------------

/// Canonical normalized form of a universe level expression:
/// represents `max(k, p_1 + k_1, p_2 + k_2, ...)` where `k` is the base constant offset.
#[derive(Clone, Debug, PartialEq, Eq)]
struct NormLevel {
    const_offset: usize,
    /// Set of `(param_name, additive_offset)` representing `Param(p) + k_i`.
    params: BTreeSet<(String, usize)>,
}

impl NormLevel {
    fn zero() -> Self {
        Self {
            const_offset: 0,
            params: BTreeSet::new(),
        }
    }

    fn param(name: String) -> Self {
        let mut params = BTreeSet::new();
        params.insert((name, 0));
        Self {
            const_offset: 0,
            params,
        }
    }

    fn add_offset(&self, k: usize) -> Self {
        let params = self
            .params
            .iter()
            .map(|(name, off)| (name.clone(), off + k))
            .collect();
        Self {
            const_offset: self.const_offset + k,
            params,
        }
    }

    fn max_with(&self, other: &Self) -> Self {
        let const_offset = self.const_offset.max(other.const_offset);
        let mut params = BTreeSet::new();

        let mut all_names = BTreeSet::new();
        for (name, _) in &self.params {
            all_names.insert(name.clone());
        }
        for (name, _) in &other.params {
            all_names.insert(name.clone());
        }

        for name in all_names {
            let max_off_self = self
                .params
                .iter()
                .filter(|(n, _)| n == &name)
                .map(|(_, off)| *off)
                .max();
            let max_off_other = other
                .params
                .iter()
                .filter(|(n, _)| n == &name)
                .map(|(_, off)| *off)
                .max();

            let best = match (max_off_self, max_off_other) {
                (Some(a), Some(b)) => a.max(b),
                (Some(a), None) => a,
                (None, Some(b)) => b,
                (None, None) => unreachable!(),
            };

            params.insert((name, best));
        }

        Self {
            const_offset,
            params,
        }
    }

    fn is_definitely_zero(&self) -> bool {
        self.const_offset == 0 && self.params.is_empty()
    }

    fn is_definitely_nonzero(&self) -> bool {
        self.const_offset >= 1
    }
}

/// Normalize a `UnivLevel` into a list of `NormLevel` forms.
fn normalize_level(level: &UnivLevel) -> Vec<NormLevel> {
    match level {
        UnivLevel::Zero(_) => vec![NormLevel::zero()],
        UnivLevel::Param(p) => vec![NormLevel::param(p.name.clone())],
        UnivLevel::Succ(s) => normalize_level(&s.pred)
            .into_iter()
            .map(|nl| nl.add_offset(1))
            .collect(),
        UnivLevel::Max(m) => {
            let lefts = normalize_level(&m.left);
            let rights = normalize_level(&m.right);
            let mut res = Vec::with_capacity(lefts.len() * rights.len());
            for l in &lefts {
                for r in &rights {
                    res.push(l.max_with(r));
                }
            }
            res
        }
        UnivLevel::IMax(im) => {
            let rights = normalize_level(&im.right);
            if rights.iter().all(NormLevel::is_definitely_zero) {
                return vec![NormLevel::zero()];
            }
            let lefts = normalize_level(&im.left);
            let mut res = Vec::with_capacity(lefts.len() * rights.len() + 1);
            // If `right` is not guaranteed >= 1, include the `right == 0 => 0` branch.
            if !rights.iter().all(NormLevel::is_definitely_nonzero) {
                res.push(NormLevel::zero());
            }
            for l in &lefts {
                for r in &rights {
                    res.push(l.max_with(r));
                }
            }
            res
        }
    }
}

/// Check whether two universe levels are definitionally equal.
///
/// Decides equality modulo:
/// - Associativity, commutativity, and idempotence of `max` (`max(u, u) == u`, `max(u, v) == max(v, u)`)
/// - `Zero` identity (`max(0, u) == u`)
/// - `Succ` distribution (`succ(max(u, v)) == max(succ(u), succ(v))`)
/// - `IMax` zero/succ reduction (`imax(u, 0) == 0`, `imax(u, succ(v)) == max(u, succ(v))`)
pub fn is_level_def_eq(l1: &UnivLevel, l2: &UnivLevel) -> bool {
    if l1 == l2 {
        return true;
    }

    let mut param_names = BTreeSet::new();
    collect_level_params(l1, &mut param_names);
    collect_level_params(l2, &mut param_names);

    let params: Vec<String> = param_names.into_iter().collect();
    check_level_eq_with_splits(l1, l2, &params, 0)
}

fn collect_level_params(level: &UnivLevel, acc: &mut BTreeSet<String>) {
    match level {
        UnivLevel::Zero(_) => {}
        UnivLevel::Param(p) => {
            acc.insert(p.name.clone());
        }
        UnivLevel::Succ(s) => collect_level_params(&s.pred, acc),
        UnivLevel::Max(m) => {
            collect_level_params(&m.left, acc);
            collect_level_params(&m.right, acc);
        }
        UnivLevel::IMax(im) => {
            collect_level_params(&im.left, acc);
            collect_level_params(&im.right, acc);
        }
    }
}

/// Exact decision procedure for universe level equality via `0` vs `Succ(p)` case-splitting
/// on free universe parameters.
fn check_level_eq_with_splits(
    l1: &UnivLevel,
    l2: &UnivLevel,
    params: &[String],
    idx: usize,
) -> bool {
    if idx == params.len() {
        return normalize_level(l1) == normalize_level(l2);
    }

    let param = &params[idx];
    // Branch 1: `param = 0`
    let l1_zero = subst_level_param(l1, param, &UnivLevel::zero());
    let l2_zero = subst_level_param(l2, param, &UnivLevel::zero());
    if !check_level_eq_with_splits(&l1_zero, &l2_zero, params, idx + 1) {
        return false;
    }

    // Branch 2: `param = Succ(param)` (represents any level >= 1)
    let succ_param = UnivLevel::succ(Arc::new(UnivLevel::param(param.clone())));
    let l1_succ = subst_level_param(l1, param, &succ_param);
    let l2_succ = subst_level_param(l2, param, &succ_param);
    check_level_eq_with_splits(&l1_succ, &l2_succ, params, idx + 1)
}

fn subst_level_param(level: &UnivLevel, target: &str, replacement: &UnivLevel) -> UnivLevel {
    match level {
        UnivLevel::Zero(_) => level.clone(),
        UnivLevel::Param(p) if p.name == target => replacement.clone(),
        UnivLevel::Param(_) => level.clone(),
        UnivLevel::Succ(s) => {
            UnivLevel::succ(Arc::new(subst_level_param(&s.pred, target, replacement)))
        }
        UnivLevel::Max(m) => UnivLevel::max(
            Arc::new(subst_level_param(&m.left, target, replacement)),
            Arc::new(subst_level_param(&m.right, target, replacement)),
        ),
        UnivLevel::IMax(im) => UnivLevel::imax(
            Arc::new(subst_level_param(&im.left, target, replacement)),
            Arc::new(subst_level_param(&im.right, target, replacement)),
        ),
    }
}

// ---------------------------------------------------------------------------
// Expression Definitional Equality (Stage 1: WHNF + Structural + Binder)
// ---------------------------------------------------------------------------

/// Create a collision-free fresh free variable for opening binders during equality checks.
#[inline]
fn fresh_eq_fvar() -> Expr {
    Expr::fvar(format!("#eq.{}", Uuid::new_v4()))
}

/// Check whether two expressions `t` and `s` are definitionally equal under `env`.
pub fn is_def_eq(t: &Expr, s: &Expr, env: &Environment) -> bool {
    is_def_eq_arc(Arc::new(t.clone()), Arc::new(s.clone()), env)
}

/// Core definitional equality check operating on shared `Arc<Expr>` nodes.
pub(crate) fn is_def_eq_arc(t: Arc<Expr>, s: Arc<Expr>, env: &Environment) -> bool {
    // 1. Fast pointer / structural equality check before any reduction.
    if Arc::ptr_eq(&t, &s) || *t == *s {
        return true;
    }

    // [Stage 2 Hook]: Proof Irrelevance
    // If `t` and `s` have types in `Prop` (`Sort(0)`) whose types are definitionally equal,
    // return `true`.

    // 2. Reduce both sides to Weak Head Normal Form (WHNF).
    let t_whnf = whnf_arc(t, env);
    let s_whnf = whnf_arc(s, env);

    // Re-check pointer / structural equality after WHNF reduction.
    if Arc::ptr_eq(&t_whnf, &s_whnf) || *t_whnf == *s_whnf {
        return true;
    }

    // 3. Structural comparison on WHNF heads.
    if is_def_eq_whnf(&t_whnf, &s_whnf, env) {
        return true;
    }

    // [Stage 2 Hook]: Eta-equivalence (`Lam` vs non-`Lam` when type reduces to `Pi`)
    // [Stage 2 Hook]: Nat literal vs `Nat.zero` / `Nat.succ`

    false
}

/// Compare two expressions that are already in Weak Head Normal Form.
fn is_def_eq_whnf(t: &Expr, s: &Expr, env: &Environment) -> bool {
    match (t, s) {
        (Expr::Sort(s1), Expr::Sort(s2)) => is_level_def_eq(&s1.level, &s2.level),

        (Expr::FVar(v1), Expr::FVar(v2)) => v1.name == v2.name,

        (Expr::BVar(b1), Expr::BVar(b2)) => b1.idx == b2.idx,

        (Expr::MVar(m1), Expr::MVar(m2)) => m1.id == m2.id,

        (Expr::Const(c1), Expr::Const(c2)) => {
            c1.name == c2.name
                && c1.levels.len() == c2.levels.len()
                && c1
                    .levels
                    .iter()
                    .zip(c2.levels.iter())
                    .all(|(l1, l2)| is_level_def_eq(l1, l2))
        }

        (Expr::Lit(l1), Expr::Lit(l2)) => is_def_eq_literal(&l1.lit, &l2.lit, env),

        (Expr::App(a1), Expr::App(a2)) => {
            is_def_eq_arc(Arc::clone(&a1.f), Arc::clone(&a2.f), env)
                && is_def_eq_arc(Arc::clone(&a1.arg), Arc::clone(&a2.arg), env)
        }

        (Expr::Lam(l1), Expr::Lam(l2)) => {
            if !is_def_eq_arc(Arc::clone(&l1.t), Arc::clone(&l2.t), env) {
                return false;
            }
            let fvar = fresh_eq_fvar();
            let body1 = Arc::new(instantiate_bvar(&l1.body, &fvar));
            let body2 = Arc::new(instantiate_bvar(&l2.body, &fvar));
            is_def_eq_arc(body1, body2, env)
        }

        (Expr::Pi(p1), Expr::Pi(p2)) => {
            if !is_def_eq_arc(Arc::clone(&p1.t), Arc::clone(&p2.t), env) {
                return false;
            }
            let fvar = fresh_eq_fvar();
            let body1 = Arc::new(instantiate_bvar(&p1.body, &fvar));
            let body2 = Arc::new(instantiate_bvar(&p2.body, &fvar));
            is_def_eq_arc(body1, body2, env)
        }

        // `whnf_arc` always zeta-reduces `Expr::Let`, so this arm is defensive only.
        (Expr::Let(l1), Expr::Let(l2)) => {
            if !is_def_eq_arc(Arc::clone(&l1.t), Arc::clone(&l2.t), env)
                || !is_def_eq_arc(Arc::clone(&l1.value), Arc::clone(&l2.value), env)
            {
                return false;
            }
            let fvar = fresh_eq_fvar();
            let body1 = Arc::new(instantiate_bvar(&l1.body, &fvar));
            let body2 = Arc::new(instantiate_bvar(&l2.body, &fvar));
            is_def_eq_arc(body1, body2, env)
        }

        _ => false,
    }
}

fn is_def_eq_literal(l1: &Literal, l2: &Literal, env: &Environment) -> bool {
    match (l1, l2) {
        (Literal::Nat(a), Literal::Nat(b)) => a == b,
        (Literal::Float(a), Literal::Float(b)) => a.to_bits() == b.to_bits(),
        (Literal::String(a), Literal::String(b)) => a == b,
        (Literal::Array(a), Literal::Array(b)) => {
            a.len() == b.len()
                && a.iter()
                    .zip(b.iter())
                    .all(|(ea, eb)| is_def_eq_arc(Arc::new(ea.clone()), Arc::new(eb.clone()), env))
        }
        _ => false,
    }
}
