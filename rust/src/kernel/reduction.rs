//! Reduction engine for expressions in the poussins kernel.
//!
//! Implements Weak Head Normal Form (WHNF) evaluation, including beta,
//! zeta (let-expansion), delta (constant unfolding), and iota (recursor
//! computation) reduction rules.
//!
//! Traversal uses an explicit argument spine (`Vec<Arc<Expr>>`) to achieve:
//! - Stack safety for arbitrarily deep application chains.
//! - Batch beta/iota reduction without intermediate App node allocation.
//! - Copy-on-Write sharing and O(1) early returns via `loose_bvar_range`.

use std::sync::Arc;

use crate::ast::expr::{EConst, ELam, ELet, Expr};
use crate::ast::ops::{instantiate_bvar, instantiate_level_params};
use crate::environment::declaration::Declaration;
use crate::environment::environment::Environment;

// ---------------------------------------------------------------------------
// 1-step reduction rules
// ---------------------------------------------------------------------------

/// 1-step beta reduction: `(λx. body) arg` ==> `instantiate_bvar(body, arg)`.
///
/// Takes the concrete `&ELam` struct directly (type-safe, no enum matching overhead)
/// and delegates to `instantiate_bvar`, taking advantage of `loose_bvar_range` for O(1)
/// early returns and Copy-on-Write structural sharing.
#[inline]
pub(crate) fn beta(lam: &ELam, arg: &Expr) -> Expr {
    instantiate_bvar(&lam.body, arg)
}

/// 1-step zeta reduction (let-expansion): `let x : t = value in body` ==> `instantiate_bvar(body, value)`.
///
/// Takes the concrete `&ELet` struct directly (matching `beta`'s type-safe signature)
/// and delegates to `instantiate_bvar`.
#[inline]
pub(crate) fn zeta(let_expr: &ELet) -> Expr {
    instantiate_bvar(&let_expr.body, &let_expr.value)
}

/// 1-step delta reduction: unfold a transparent `DefinitionDecl` with level instantiation.
pub(crate) fn delta(env: &Environment, c: &EConst) -> Option<Expr> {
    let Declaration::Definition(def) = env.get(&c.name)? else {
        return None;
    };
    if def.is_opaque || def.level_params.len() != c.levels.len() {
        return None;
    }
    Some(instantiate_level_params(
        &def.value,
        &def.level_params,
        &c.levels,
    ))
}

/// 1-step iota reduction: recursor computation rule on a constructor major premise.
///
/// Expected argument layout in `spine` (where `spine.last()` is argument 0):
/// `[params (num_params), motives (num_motives), minors (num_minors), indices (num_indices), major, extra...]`
///
/// When `major` reduces in WHNF to `ctor params_ctor fields...` matching a `RecursorRule`,
/// consumes `num_params + num_motives + num_minors + num_indices + 1` arguments from `spine`
/// and returns `rhs[levels] params... motives... minors... fields...`.
pub(crate) fn iota(env: &Environment, rec_const: &EConst, spine: &mut Vec<Arc<Expr>>) -> Option<Expr> {
    let Declaration::Recursor(rec) = env.get(&rec_const.name)? else {
        return None;
    };
    if rec.level_params.len() != rec_const.levels.len() {
        return None;
    }

    let major_idx = rec.num_params + rec.num_motives + rec.num_minors + rec.num_indices;
    if spine.len() <= major_idx {
        return None;
    }

    // Access major premise at logical index `major_idx` without draining `spine` yet.
    let major_pos = spine.len() - 1 - major_idx;
    let major_whnf = whnf_arc(Arc::clone(&spine[major_pos]), env);

    // Unwind constructor head and its arguments iteratively.
    let mut ctor_args: Vec<Arc<Expr>> = Vec::new();
    let mut ctor_head = major_whnf;
    while let Expr::App(ref app) = *ctor_head {
        ctor_args.push(Arc::clone(&app.arg));
        ctor_head = Arc::clone(&app.f);
    }
    ctor_args.reverse();

    let Expr::Const(ref ctor_const) = *ctor_head else {
        return None;
    };
    let Declaration::Constructor(ctor_decl) = env.get(&ctor_const.name)? else {
        return None;
    };
    if ctor_decl.level_params.len() != ctor_const.levels.len() {
        return None;
    }

    let rule = rec
        .rules
        .iter()
        .find(|r| r.constructor_name == ctor_const.name)?;

    // Constructor arguments consist of inductive parameters followed by constructor fields.
    if ctor_args.len() != rec.num_params + rule.num_fields {
        return None;
    }

    // Instantiate universe level parameters on the rule's right-hand side.
    let mut rhs = Arc::new(instantiate_level_params(
        &rule.rhs,
        &rec.level_params,
        &rec_const.levels,
    ));

    // Consume `params`, `motives`, `minors` (popping from `spine` yields them in forward order)
    // and apply them to `rhs`.
    let prefix_count = rec.num_params + rec.num_motives + rec.num_minors;
    for _ in 0..prefix_count {
        let arg = spine.pop().unwrap();
        rhs = Arc::new(Expr::app(rhs, arg));
    }

    // Discard `indices` and `major` from `spine`.
    spine.truncate(spine.len() - (rec.num_indices + 1));

    // Apply constructor fields (skipping the first `rec.num_params` inductive parameters).
    for field in ctor_args.into_iter().skip(rec.num_params) {
        rhs = Arc::new(Expr::app(rhs, field));
    }

    Some(Arc::try_unwrap(rhs).unwrap_or_else(|a| (*a).clone()))
}

// ---------------------------------------------------------------------------
// WHNF (Weak Head Normal Form) Engine
// ---------------------------------------------------------------------------

/// Reduce an expression to Weak Head Normal Form (WHNF) iteratively under `env`.
///
/// This evaluates the expression until its outermost constructor is a value
/// (e.g. Sort, Lam, Pi, Lit) or a neutral head applied to arguments that cannot
/// reduce further.
///
/// Deep application chains are flattened onto an explicit spine stack, avoiding
/// call-stack recursion and eliminating intermediate `EApp` allocations.
pub fn whnf(expr: &Expr, env: &Environment) -> Expr {
    // Fast path: atomic and canonical head forms cannot be reduced at the head.
    match expr {
        Expr::Sort(_)
        | Expr::FVar(_)
        | Expr::BVar(_)
        | Expr::Lam(_)
        | Expr::Pi(_)
        | Expr::Lit(_)
        | Expr::MVar(_) => {
            return expr.clone();
        }
        _ => {}
    }

    let arc_res = whnf_core(Arc::new(expr.clone()), env);
    Arc::try_unwrap(arc_res).unwrap_or_else(|a| (*a).clone())
}

/// Reduce a shared `Arc<Expr>` to WHNF under `env`, preserving Arc identity when possible.
pub fn whnf_arc(expr: Arc<Expr>, env: &Environment) -> Arc<Expr> {
    match *expr {
        Expr::Sort(_)
        | Expr::FVar(_)
        | Expr::BVar(_)
        | Expr::Lam(_)
        | Expr::Pi(_)
        | Expr::Lit(_)
        | Expr::MVar(_) => {
            return expr;
        }
        _ => {}
    }

    whnf_core(expr, env)
}

/// Core iterative WHNF evaluation loop.
fn whnf_core(mut curr: Arc<Expr>, env: &Environment) -> Arc<Expr> {
    // The spine stores argument Arcs in reverse order:
    // For `(((f a1) a2) a3)`, unwinding pushes `a3`, then `a2`, then `a1`.
    // Thus `spine.pop()` yields `a1` first.
    let mut spine: Vec<Arc<Expr>> = Vec::new();
    let mut reduced_any = false;
    let orig = Arc::clone(&curr);

    loop {
        // 1. Flatten application spine into head `curr` and argument stack.
        while let Expr::App(ref app) = *curr {
            spine.push(Arc::clone(&app.arg));
            curr = Arc::clone(&app.f);
        }

        // 2. Dispatch on the head expression.
        match *curr {
            // --- Beta reduction: (λx. body) applied to an argument ---
            Expr::Lam(ref lam) if !spine.is_empty() => {
                let arg = spine.pop().unwrap();
                let next_term = beta(lam, &arg);
                curr = Arc::new(next_term);
                reduced_any = true;
            }

            // --- Zeta reduction: Let-binding expansion ---
            Expr::Let(ref let_expr) => {
                let next_term = zeta(let_expr);
                curr = Arc::new(next_term);
                reduced_any = true;
            }

            // --- Delta / Iota reduction: Constant unfolding or Recursor computation ---
            Expr::Const(ref c) => {
                if let Some(unfolded) = delta(env, c) {
                    curr = Arc::new(unfolded);
                    reduced_any = true;
                } else if let Some(reduced) = iota(env, c, &mut spine) {
                    curr = Arc::new(reduced);
                    reduced_any = true;
                } else {
                    break;
                }
            }

            // --- Head is irreducible in WHNF ---
            _ => break,
        }
    }

    // Fast return: if no reduction was performed, return the original Arc directly.
    // This ensures neutral application chains (e.g. `(f a b)`) require zero reconstruction.
    if !reduced_any {
        return orig;
    }

    // 3. Reconstruct remaining application spine from left to right.
    let mut result = curr;
    while let Some(arg) = spine.pop() {
        result = Arc::new(Expr::app(result, arg));
    }

    result
}
