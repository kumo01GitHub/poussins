use std::sync::Arc;

use crate::ast::expr::{EApp, EBVar, EFVar, ELet, ELit, ELam, EPi, Expr, Literal};
use crate::ast::univ_level::UnivLevel;

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
/// target index for `instantiate_bvar`, binding depth for `bind`). It returns
/// `Some(e)` to replace the leaf, or `None` to keep it as-is (cloned).
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
// Iterative universe level instantiation
// ---------------------------------------------------------------------------

/// Instantiate universe level parameters `params` with `args` in `level` iteratively.
fn instantiate_params(level: &UnivLevel, params: &[String], args: &[UnivLevel]) -> UnivLevel {
    enum LevelTask<'a> {
        Visit(&'a UnivLevel),
        BuildSucc(&'a UnivLevel),
        BuildMax(&'a UnivLevel),
        BuildIMax(&'a UnivLevel),
    }

    let mut tasks = vec![LevelTask::Visit(level)];
    let mut results: Vec<UnivLevel> = Vec::new();

    while let Some(task) = tasks.pop() {
        match task {
            LevelTask::Visit(cur) => match cur {
                UnivLevel::Zero(_) => results.push(cur.clone()),
                UnivLevel::Param(p) => {
                    if let Some(pos) = params.iter().position(|name| name == &p.name) {
                        results.push(args[pos].clone());
                    } else {
                        results.push(cur.clone());
                    }
                }
                UnivLevel::Succ(s) => {
                    tasks.push(LevelTask::BuildSucc(cur));
                    tasks.push(LevelTask::Visit(&s.pred));
                }
                UnivLevel::Max(m) => {
                    tasks.push(LevelTask::BuildMax(cur));
                    tasks.push(LevelTask::Visit(&m.right));
                    tasks.push(LevelTask::Visit(&m.left));
                }
                UnivLevel::IMax(im) => {
                    tasks.push(LevelTask::BuildIMax(cur));
                    tasks.push(LevelTask::Visit(&im.right));
                    tasks.push(LevelTask::Visit(&im.left));
                }
            },
            LevelTask::BuildSucc(orig) => {
                let pred = results.pop().unwrap();
                if let UnivLevel::Succ(s) = orig {
                    if pred == *s.pred {
                        results.push(orig.clone());
                        continue;
                    }
                }
                results.push(UnivLevel::succ(Arc::new(pred)));
            }
            LevelTask::BuildMax(orig) => {
                let right = results.pop().unwrap();
                let left = results.pop().unwrap();
                if let UnivLevel::Max(m) = orig {
                    if left == *m.left && right == *m.right {
                        results.push(orig.clone());
                        continue;
                    }
                }
                results.push(UnivLevel::max(Arc::new(left), Arc::new(right)));
            }
            LevelTask::BuildIMax(orig) => {
                let right = results.pop().unwrap();
                let left = results.pop().unwrap();
                if let UnivLevel::IMax(im) = orig {
                    if left == *im.left && right == *im.right {
                        results.push(orig.clone());
                        continue;
                    }
                }
                results.push(UnivLevel::imax(Arc::new(left), Arc::new(right)));
            }
        }
    }

    results.pop().unwrap()
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
                    .unwrap_or_else(|| {
                        panic!("de Bruijn index underflow during shift: idx={idx}, delta={delta}")
                    });
                Some(Expr::bvar(shifted))
            } else {
                None // keep as-is
            }
        }
        _ => None, // Sort, FVar, Const, MVar, non-array Lit — unchanged
    })
}

/// Instantiate `BVar(0)` with `replacement` in `expr`, shifting `replacement`
/// appropriately under binders and decrementing outer bound variables (`idx > 0`) by 1.
///
/// If `expr` is closed (`loose_bvar_range() == 0`), instantiation is a no-op and returns in $O(1)$.
pub fn instantiate_bvar(expr: &Expr, replacement: &Expr) -> Expr {
    if expr.loose_bvar_range() == 0 {
        return expr.clone();
    }

    traverse(expr, 0, &|cur, cur_target| match cur {
        Expr::BVar(EBVar { idx }) => {
            if *idx == cur_target {
                let depth_offset = cur_target as isize;
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

/// Instantiate universe level parameters `params` with `args` in `expr` iteratively.
///
/// Reuses existing `Arc` nodes whenever subexpressions are unaffected (Copy-on-Write).
pub fn instantiate_univ_level(expr: &Expr, params: &[String], args: &[UnivLevel]) -> Expr {
    if params.is_empty() || params.len() != args.len() {
        return expr.clone();
    }

    traverse(expr, 0, &|cur, _depth| match cur {
        Expr::Sort(s) => {
            let new_lvl = instantiate_params(&s.level, params, args);
            if new_lvl == s.level {
                None
            } else {
                Some(Expr::sort(new_lvl))
            }
        }
        Expr::Const(c) => {
            if c.levels.is_empty() {
                return None;
            }
            let mut changed = false;
            let mut new_levels = Vec::with_capacity(c.levels.len());
            for lvl in &c.levels {
                let inst = instantiate_params(lvl, params, args);
                if inst != *lvl {
                    changed = true;
                }
                new_levels.push(inst);
            }
            if changed {
                Some(Expr::const_(c.name.clone(), new_levels))
            } else {
                None
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
