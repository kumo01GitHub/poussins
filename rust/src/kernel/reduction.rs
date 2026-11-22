//! Reduction engine for expressions in the poussins kernel.
//!
//! Implements Weak Head Normal Form (WHNF) evaluation, including beta,
//! zeta (let-expansion), and future delta/iota reduction rules.
//!
//! Traversal uses an explicit argument spine (`Vec<Arc<Expr>>`) to achieve:
//! - Stack safety for arbitrarily deep application chains.
//! - Batch beta-reduction without intermediate App node allocation.
//! - Copy-on-Write sharing and O(1) early returns via `loose_bvar_range`.

use std::sync::Arc;

use crate::ast::expr::{ELam, ELet, Expr};
use crate::ast::ops::subst;

// ---------------------------------------------------------------------------
// 1-step reduction rules
// ---------------------------------------------------------------------------

/// 1-step beta reduction: `(λx. body) arg` ==> `subst(body, 0, arg)`.
///
/// Takes the concrete `&ELam` struct directly (type-safe, no enum matching overhead)
/// and delegates to `subst`, taking advantage of `loose_bvar_range` for O(1)
/// early returns and Copy-on-Write structural sharing.
#[inline]
pub(crate) fn beta(lam: &ELam, arg: &Expr) -> Expr {
    subst(&lam.body, 0, arg)
}

/// 1-step zeta reduction (let-expansion): `let x : t = value in body` ==> `subst(body, 0, value)`.
///
/// Takes the concrete `&ELet` struct directly (matching `beta`'s type-safe signature)
/// and delegates to `subst`, taking advantage of `loose_bvar_range` for O(1)
/// early returns and Copy-on-Write structural sharing.
#[inline]
pub(crate) fn zeta(let_expr: &ELet) -> Expr {
    subst(&let_expr.body, 0, &let_expr.value)
}

// ---------------------------------------------------------------------------
// WHNF (Weak Head Normal Form) Engine
// ---------------------------------------------------------------------------

/// Reduce an expression to Weak Head Normal Form (WHNF) iteratively.
///
/// This evaluates the expression until its outermost constructor is a value
/// (e.g. Sort, Lam, Pi, Lit) or a neutral head applied to arguments that cannot
/// reduce further.
///
/// Deep application chains are flattened onto an explicit spine stack, avoiding
/// call-stack recursion and eliminating intermediate `EApp` allocations.
pub fn whnf(expr: &Expr) -> Expr {
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

    let arc_res = whnf_core(Arc::new(expr.clone()));
    Arc::try_unwrap(arc_res).unwrap_or_else(|a| (*a).clone())
}

/// Reduce a shared `Arc<Expr>` to WHNF, preserving Arc identity when possible.
pub fn whnf_arc(expr: Arc<Expr>) -> Arc<Expr> {
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

    whnf_core(expr)
}

/// Core iterative WHNF evaluation loop.
fn whnf_core(mut curr: Arc<Expr>) -> Arc<Expr> {
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
                // Continue loop: `next_term` may be another Lam or an App chain.
            }

            // --- Zeta reduction: Let-binding expansion ---
            Expr::Let(ref let_expr) => {
                let next_term = zeta(let_expr);
                curr = Arc::new(next_term);
                reduced_any = true;
            }

            // --- Delta reduction stub: Constant definition unfolding ---
            // (When Environment integration is ready)

            // --- Iota reduction stub: Recursor computation rules ---
            // (When inductive recursor rules are integrated)

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
    // Remaining arguments in `spine` are [a_n, ..., a_{consumed+1}].
    // Popping yields a_{consumed+1}, then a_{consumed+2}, ..., up to a_n.
    let mut result = curr;
    while let Some(arg) = spine.pop() {
        result = Arc::new(Expr::app(result, arg));
    }

    result
}
