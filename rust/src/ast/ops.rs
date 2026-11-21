use std::sync::Arc;

use crate::ast::expr::{Expr, Literal};

/// Shift de Bruijn indices >= `cutoff` by `delta` (supports positive and negative offsets).
///
/// Bound variables with `idx < cutoff` are bound locally inside the expression and remain untouched.
pub fn shift(expr: &Expr, delta: isize, cutoff: usize) -> Expr {
    if delta == 0 {
        return expr.clone();
    }

    enum Task<'a> {
        Visit(&'a Expr, usize),
        BuildApp,
        BuildLam(String),
        BuildPi(String),
        BuildLet(String),
        BuildLitArray(usize),
    }

    let mut tasks = vec![Task::Visit(expr, cutoff)];
    let mut results: Vec<Arc<Expr>> = Vec::new();

    while let Some(task) = tasks.pop() {
        match task {
            Task::Visit(cur, cur_cutoff) => match cur {
                Expr::BVar(idx) => {
                    if *idx >= cur_cutoff {
                        let shifted = idx
                            .checked_add_signed(delta)
                            .expect("de Bruijn index underflow during shift");
                        results.push(Arc::new(Expr::BVar(shifted)));
                    } else {
                        results.push(Arc::new(Expr::BVar(*idx)));
                    }
                }
                Expr::Sort(_) | Expr::FVar(_) | Expr::Const(_, _) | Expr::MVar(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::Lit(Literal::Array(items)) => {
                    tasks.push(Task::BuildLitArray(items.len()));
                    for item in items.iter().rev() {
                        tasks.push(Task::Visit(item, cur_cutoff));
                    }
                }
                Expr::Lit(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::App(fn_expr, arg) => {
                    tasks.push(Task::BuildApp);
                    tasks.push(Task::Visit(arg, cur_cutoff));
                    tasks.push(Task::Visit(fn_expr, cur_cutoff));
                }
                Expr::Lam(var, domain, body) => {
                    tasks.push(Task::BuildLam(var.clone()));
                    tasks.push(Task::Visit(body, cur_cutoff + 1));
                    tasks.push(Task::Visit(domain, cur_cutoff));
                }
                Expr::Pi(var, domain, body) => {
                    tasks.push(Task::BuildPi(var.clone()));
                    tasks.push(Task::Visit(body, cur_cutoff + 1));
                    tasks.push(Task::Visit(domain, cur_cutoff));
                }
                Expr::Let(var, var_type, value, body) => {
                    tasks.push(Task::BuildLet(var.clone()));
                    tasks.push(Task::Visit(body, cur_cutoff + 1));
                    tasks.push(Task::Visit(value, cur_cutoff));
                    tasks.push(Task::Visit(var_type, cur_cutoff));
                }
            },
            Task::BuildApp => {
                let arg = results.pop().unwrap();
                let fn_expr = results.pop().unwrap();
                results.push(Arc::new(Expr::App(fn_expr, arg)));
            }
            Task::BuildLam(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::Lam(var, domain, body)));
            }
            Task::BuildPi(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::Pi(var, domain, body)));
            }
            Task::BuildLet(var) => {
                let body = results.pop().unwrap();
                let value = results.pop().unwrap();
                let var_type = results.pop().unwrap();
                results.push(Arc::new(Expr::Let(var, var_type, value, body)));
            }
            Task::BuildLitArray(len) => {
                let start = results.len() - len;
                let items: Vec<Expr> = results
                    .drain(start..)
                    .map(|arc| Arc::try_unwrap(arc).unwrap_or_else(|a| (*a).clone()))
                    .collect();
                results.push(Arc::new(Expr::Lit(Literal::Array(items))));
            }
        }
    }

    let root = results.pop().unwrap();
    Arc::try_unwrap(root).unwrap_or_else(|arc| (*arc).clone())
}

/// Substitute `BVar(target)` with `replacement` in `expr`, shifting `replacement`
/// appropriately under binders and decrementing outer bound variables (`idx > target`) by 1.
///
/// For standard beta-reduction `(λx. body) arg`, call `subst(&body, 0, &arg)`.
pub fn subst(expr: &Expr, target: usize, replacement: &Expr) -> Expr {
    enum Task<'a> {
        Visit(&'a Expr, usize),
        BuildApp,
        BuildLam(String),
        BuildPi(String),
        BuildLet(String),
        BuildLitArray(usize),
    }

    let mut tasks = vec![Task::Visit(expr, target)];
    let mut results: Vec<Arc<Expr>> = Vec::new();

    while let Some(task) = tasks.pop() {
        match task {
            Task::Visit(cur, cur_target) => match cur {
                Expr::BVar(idx) => {
                    if *idx == cur_target {
                        let depth_offset = (cur_target - target) as isize;
                        results.push(Arc::new(shift(replacement, depth_offset, 0)));
                    } else if *idx > cur_target {
                        results.push(Arc::new(Expr::BVar(idx - 1)));
                    } else {
                        results.push(Arc::new(Expr::BVar(*idx)));
                    }
                }
                Expr::Sort(_) | Expr::FVar(_) | Expr::Const(_, _) | Expr::MVar(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::Lit(Literal::Array(items)) => {
                    tasks.push(Task::BuildLitArray(items.len()));
                    for item in items.iter().rev() {
                        tasks.push(Task::Visit(item, cur_target));
                    }
                }
                Expr::Lit(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::App(fn_expr, arg) => {
                    tasks.push(Task::BuildApp);
                    tasks.push(Task::Visit(arg, cur_target));
                    tasks.push(Task::Visit(fn_expr, cur_target));
                }
                Expr::Lam(var, domain, body) => {
                    tasks.push(Task::BuildLam(var.clone()));
                    tasks.push(Task::Visit(body, cur_target + 1));
                    tasks.push(Task::Visit(domain, cur_target));
                }
                Expr::Pi(var, domain, body) => {
                    tasks.push(Task::BuildPi(var.clone()));
                    tasks.push(Task::Visit(body, cur_target + 1));
                    tasks.push(Task::Visit(domain, cur_target));
                }
                Expr::Let(var, var_type, value, body) => {
                    tasks.push(Task::BuildLet(var.clone()));
                    tasks.push(Task::Visit(body, cur_target + 1));
                    tasks.push(Task::Visit(value, cur_target));
                    tasks.push(Task::Visit(var_type, cur_target));
                }
            },
            Task::BuildApp => {
                let arg = results.pop().unwrap();
                let fn_expr = results.pop().unwrap();
                results.push(Arc::new(Expr::App(fn_expr, arg)));
            }
            Task::BuildLam(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::Lam(var, domain, body)));
            }
            Task::BuildPi(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::Pi(var, domain, body)));
            }
            Task::BuildLet(var) => {
                let body = results.pop().unwrap();
                let value = results.pop().unwrap();
                let var_type = results.pop().unwrap();
                results.push(Arc::new(Expr::Let(var, var_type, value, body)));
            }
            Task::BuildLitArray(len) => {
                let start = results.len() - len;
                let items: Vec<Expr> = results
                    .drain(start..)
                    .map(|arc| Arc::try_unwrap(arc).unwrap_or_else(|a| (*a).clone()))
                    .collect();
                results.push(Arc::new(Expr::Lit(Literal::Array(items))));
            }
        }
    }

    let root = results.pop().unwrap();
    Arc::try_unwrap(root).unwrap_or_else(|arc| (*arc).clone())
}

/// Bind a free variable name to a de Bruijn index iteratively (stack-safe).
///
/// Traverses the expression using an explicit stack, replacing all occurrences
/// of `FVar(name)` with `BVar(depth)` relative to the binding depth.
pub fn bind(expr: &Expr, name: &str) -> Expr {
    enum Task<'a> {
        Visit(&'a Expr, usize),
        BuildApp,
        BuildLam(String),
        BuildPi(String),
        BuildLet(String),
        BuildLitArray(usize),
    }

    let mut tasks = vec![Task::Visit(expr, 0)];
    let mut results: Vec<Arc<Expr>> = Vec::new();

    while let Some(task) = tasks.pop() {
        match task {
            Task::Visit(cur, depth) => match cur {
                Expr::FVar(n) => {
                    if n == name {
                        results.push(Arc::new(Expr::BVar(depth)));
                    } else {
                        results.push(Arc::new(cur.clone()));
                    }
                }
                Expr::BVar(_) | Expr::Sort(_) | Expr::Const(_, _) | Expr::MVar(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::Lit(Literal::Array(items)) => {
                    tasks.push(Task::BuildLitArray(items.len()));
                    for item in items.iter().rev() {
                        tasks.push(Task::Visit(item, depth));
                    }
                }
                Expr::Lit(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::App(fn_expr, arg) => {
                    tasks.push(Task::BuildApp);
                    tasks.push(Task::Visit(arg, depth));
                    tasks.push(Task::Visit(fn_expr, depth));
                }
                Expr::Lam(var, domain, body) => {
                    tasks.push(Task::BuildLam(var.clone()));
                    tasks.push(Task::Visit(body, depth + 1));
                    tasks.push(Task::Visit(domain, depth));
                }
                Expr::Pi(var, domain, body) => {
                    tasks.push(Task::BuildPi(var.clone()));
                    tasks.push(Task::Visit(body, depth + 1));
                    tasks.push(Task::Visit(domain, depth));
                }
                Expr::Let(var, var_type, value, body) => {
                    tasks.push(Task::BuildLet(var.clone()));
                    tasks.push(Task::Visit(body, depth + 1));
                    tasks.push(Task::Visit(value, depth));
                    tasks.push(Task::Visit(var_type, depth));
                }
            },
            Task::BuildApp => {
                let arg = results.pop().unwrap();
                let fn_expr = results.pop().unwrap();
                results.push(Arc::new(Expr::App(fn_expr, arg)));
            }
            Task::BuildLam(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::Lam(var, domain, body)));
            }
            Task::BuildPi(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::Pi(var, domain, body)));
            }
            Task::BuildLet(var) => {
                let body = results.pop().unwrap();
                let value = results.pop().unwrap();
                let var_type = results.pop().unwrap();
                results.push(Arc::new(Expr::Let(var, var_type, value, body)));
            }
            Task::BuildLitArray(len) => {
                let start = results.len() - len;
                let items: Vec<Expr> = results
                    .drain(start..)
                    .map(|arc| Arc::try_unwrap(arc).unwrap_or_else(|a| (*a).clone()))
                    .collect();
                results.push(Arc::new(Expr::Lit(Literal::Array(items))));
            }
        }
    }

    let root = results.pop().unwrap();
    Arc::try_unwrap(root).unwrap_or_else(|arc| (*arc).clone())
}
