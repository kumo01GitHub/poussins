use std::sync::Arc;

use crate::ast::expr::{EApp, EBVar, EFVar, ELet, ELit, ELam, EPi, Expr, Literal};

// ---------------------------------------------------------------------------
// Common iterative traversal framework with Copy-on-Write (Maximal Sharing)
// ---------------------------------------------------------------------------

/// Unwrap a single-owner `Arc`, or clone the inner value if shared.
#[inline]
fn arc_unwrap_or_clone<T: Clone>(arc: Arc<T>) -> T {
    Arc::try_unwrap(arc).unwrap_or_else(|a| (*a).clone())
}

/// A leaf-transform function receives the current expression and a depth
/// parameter (whose semantics depend on the caller — cutoff for `shift`,
/// target index for `subst`, binding depth for `bind`). It returns `Some(e)`
/// to replace the leaf, or `None` to keep it as-is (cloned).
type LeafFn<'a> = &'a dyn Fn(&Expr, usize) -> Option<Expr>;

/// Generic iterative expression traversal with Copy-on-Write sharing.
///
/// Walks the AST with an explicit task/result stack (stack-safe for deeply
/// nested terms). Composite nodes (App, Lam, Pi, Let, Lit-Array) check whether
/// their children were modified; if children are unchanged (by pointer equality
/// or value equality), the original `Arc` is reused without heap allocation.
fn traverse(expr: &Expr, initial_depth: usize, leaf_fn: LeafFn<'_>) -> Expr {
    enum Task<'a> {
        Visit(&'a Expr, usize),
        ReconstructApp(&'a Arc<EApp>),
        ReconstructLam(&'a Arc<ELam>),
        ReconstructPi(&'a Arc<EPi>),
        ReconstructLet(&'a Arc<ELet>),
        ReconstructLitArray(&'a [Expr]),
    }

    let mut tasks = vec![Task::Visit(expr, initial_depth)];
    let mut results: Vec<Arc<Expr>> = Vec::new();

    while let Some(task) = tasks.pop() {
        match task {
            Task::Visit(cur, depth) => match cur {
                // --- Composite nodes: schedule reconstruction step + children ---
                Expr::App(app) => {
                    tasks.push(Task::ReconstructApp(app));
                    tasks.push(Task::Visit(&app.arg, depth));
                    tasks.push(Task::Visit(&app.f, depth));
                }
                Expr::Lam(lam) => {
                    tasks.push(Task::ReconstructLam(lam));
                    tasks.push(Task::Visit(&lam.body, depth + 1));
                    tasks.push(Task::Visit(&lam.t, depth));
                }
                Expr::Pi(pi) => {
                    tasks.push(Task::ReconstructPi(pi));
                    tasks.push(Task::Visit(&pi.body, depth + 1));
                    tasks.push(Task::Visit(&pi.t, depth));
                }
                Expr::Let(let_expr) => {
                    tasks.push(Task::ReconstructLet(let_expr));
                    tasks.push(Task::Visit(&let_expr.body, depth + 1));
                    tasks.push(Task::Visit(&let_expr.value, depth));
                    tasks.push(Task::Visit(&let_expr.t, depth));
                }
                Expr::Lit(ELit {
                    lit: Literal::Array(items),
                }) => {
                    tasks.push(Task::ReconstructLitArray(items.as_slice()));
                    for item in items.iter().rev() {
                        tasks.push(Task::Visit(item, depth));
                    }
                }
                // --- Leaf / non-recursive nodes: delegate to leaf_fn ---
                other => {
                    let result = leaf_fn(other, depth).unwrap_or_else(|| other.clone());
                    results.push(Arc::new(result));
                }
            },
            // --- Copy-on-Write Build steps: reuse original Arc if unchanged ---
            Task::ReconstructApp(orig) => {
                let arg = results.pop().unwrap();
                let fn_expr = results.pop().unwrap();
                if (Arc::ptr_eq(&orig.f, &fn_expr) || *orig.f == *fn_expr)
                    && (Arc::ptr_eq(&orig.arg, &arg) || *orig.arg == *arg)
                {
                    results.push(Arc::new(Expr::App(Arc::clone(orig))));
                } else {
                    results.push(Arc::new(Expr::app(fn_expr, arg)));
                }
            }
            Task::ReconstructLam(orig) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                if (Arc::ptr_eq(&orig.t, &domain) || *orig.t == *domain)
                    && (Arc::ptr_eq(&orig.body, &body) || *orig.body == *body)
                {
                    results.push(Arc::new(Expr::Lam(Arc::clone(orig))));
                } else {
                    results.push(Arc::new(Expr::lam(orig.var.clone(), domain, body)));
                }
            }
            Task::ReconstructPi(orig) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                if (Arc::ptr_eq(&orig.t, &domain) || *orig.t == *domain)
                    && (Arc::ptr_eq(&orig.body, &body) || *orig.body == *body)
                {
                    results.push(Arc::new(Expr::Pi(Arc::clone(orig))));
                } else {
                    results.push(Arc::new(Expr::pi(orig.var.clone(), domain, body)));
                }
            }
            Task::ReconstructLet(orig) => {
                let body = results.pop().unwrap();
                let value = results.pop().unwrap();
                let var_type = results.pop().unwrap();
                if (Arc::ptr_eq(&orig.t, &var_type) || *orig.t == *var_type)
                    && (Arc::ptr_eq(&orig.value, &value) || *orig.value == *value)
                    && (Arc::ptr_eq(&orig.body, &body) || *orig.body == *body)
                {
                    results.push(Arc::new(Expr::Let(Arc::clone(orig))));
                } else {
                    results.push(Arc::new(Expr::let_(orig.var.clone(), var_type, value, body)));
                }
            }
            Task::ReconstructLitArray(orig_items) => {
                let len = orig_items.len();
                let start = results.len() - len;
                let any_changed = results[start..]
                    .iter()
                    .zip(orig_items.iter())
                    .any(|(res, orig)| **res != *orig);
                if any_changed {
                    let items: Vec<Expr> = results
                        .drain(start..)
                        .map(arc_unwrap_or_clone)
                        .collect();
                    results.push(Arc::new(Expr::lit(Literal::Array(items))));
                } else {
                    results.truncate(start);
                    results.push(Arc::new(Expr::lit(Literal::Array(orig_items.to_vec()))));
                }
            }
        }
    }

    let root = results.pop().unwrap();
    arc_unwrap_or_clone(root)
}

// ---------------------------------------------------------------------------
// Public operations built on `traverse`
// ---------------------------------------------------------------------------

/// Shift de Bruijn indices >= `cutoff` by `delta` (supports positive and negative offsets).
///
/// Bound variables with `idx < cutoff` are bound locally inside the expression and remain untouched.
/// If `expr` has no loose bound variables >= `cutoff`, the expression is returned immediately in $O(1)$.
pub fn shift(expr: &Expr, delta: isize, cutoff: usize) -> Expr {
    if delta == 0 || expr.loose_bvar_range() <= cutoff {
        return expr.clone();
    }

    traverse(expr, cutoff, &|cur, cur_cutoff| match cur {
        Expr::BVar(EBVar { idx }) => {
            if *idx >= cur_cutoff {
                let shifted = idx
                    .checked_add_signed(delta)
                    .unwrap_or_else(|| panic!("de Bruijn index underflow during shift: idx={idx}, delta={delta}"));
                Some(Expr::bvar(shifted))
            } else {
                None // keep as-is
            }
        }
        _ => None, // Sort, FVar, Const, MVar, non-array Lit — unchanged
    })
}

/// Substitute `BVar(target)` with `replacement` in `expr`, shifting `replacement`
/// appropriately under binders and decrementing outer bound variables (`idx > target`) by 1.
///
/// If `expr` has no loose bound variables >= `target + 1`, substitution is a no-op and returns in $O(1)$.
/// For standard beta-reduction `(λx. body) arg`, call `subst(&body, 0, &arg)`.
pub fn subst(expr: &Expr, target: usize, replacement: &Expr) -> Expr {
    // Fast O(1) path: if the expression has no bound variables at or above target,
    // neither substitution nor decrementing outer variables is needed.
    if expr.loose_bvar_range() <= target {
        return expr.clone();
    }

    traverse(expr, target, &|cur, cur_target| match cur {
        Expr::BVar(EBVar { idx }) => {
            if *idx == cur_target {
                let depth_offset = (cur_target - target) as isize;
                Some(shift(replacement, depth_offset, 0))
            } else if *idx > cur_target {
                Some(Expr::bvar(idx - 1))
            } else {
                None // keep as-is
            }
        }
        _ => None,
    })
}

/// Bind a free variable name to a de Bruijn index iteratively (stack-safe).
///
/// Traverses the expression using an explicit stack, replacing all occurrences
/// of `FVar(name)` with `BVar(depth)` relative to the binding depth.
pub fn bind(expr: &Expr, name: &str) -> Expr {
    traverse(expr, 0, &|cur, depth| match cur {
        Expr::FVar(EFVar { name: n }) if n == name => Some(Expr::bvar(depth)),
        _ => None,
    })
}
