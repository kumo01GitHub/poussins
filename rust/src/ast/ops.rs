use std::sync::Arc;

use crate::ast::expr::{EBVar, EFVar, ELit, Expr, Literal};

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
                Expr::BVar(EBVar { idx }) => {
                    if *idx >= cur_cutoff {
                        let shifted = idx
                            .checked_add_signed(delta)
                            .expect("de Bruijn index underflow during shift");
                        results.push(Arc::new(Expr::bvar(shifted)));
                    } else {
                        results.push(Arc::new(Expr::bvar(*idx)));
                    }
                }
                Expr::Sort(_) | Expr::FVar(_) | Expr::Const(_) | Expr::MVar(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::Lit(ELit {
                    lit: Literal::Array(items),
                }) => {
                    tasks.push(Task::BuildLitArray(items.len()));
                    for item in items.iter().rev() {
                        tasks.push(Task::Visit(item, cur_cutoff));
                    }
                }
                Expr::Lit(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::App(app) => {
                    tasks.push(Task::BuildApp);
                    tasks.push(Task::Visit(&app.arg, cur_cutoff));
                    tasks.push(Task::Visit(&app.f, cur_cutoff));
                }
                Expr::Lam(lam) => {
                    tasks.push(Task::BuildLam(lam.var.clone()));
                    tasks.push(Task::Visit(&lam.body, cur_cutoff + 1));
                    tasks.push(Task::Visit(&lam.t, cur_cutoff));
                }
                Expr::Pi(pi) => {
                    tasks.push(Task::BuildPi(pi.var.clone()));
                    tasks.push(Task::Visit(&pi.body, cur_cutoff + 1));
                    tasks.push(Task::Visit(&pi.t, cur_cutoff));
                }
                Expr::Let(let_expr) => {
                    tasks.push(Task::BuildLet(let_expr.var.clone()));
                    tasks.push(Task::Visit(&let_expr.body, cur_cutoff + 1));
                    tasks.push(Task::Visit(&let_expr.value, cur_cutoff));
                    tasks.push(Task::Visit(&let_expr.t, cur_cutoff));
                }
            },
            Task::BuildApp => {
                let arg = results.pop().unwrap();
                let fn_expr = results.pop().unwrap();
                results.push(Arc::new(Expr::app(fn_expr, arg)));
            }
            Task::BuildLam(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::lam(var, domain, body)));
            }
            Task::BuildPi(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::pi(var, domain, body)));
            }
            Task::BuildLet(var) => {
                let body = results.pop().unwrap();
                let value = results.pop().unwrap();
                let var_type = results.pop().unwrap();
                results.push(Arc::new(Expr::let_(var, var_type, value, body)));
            }
            Task::BuildLitArray(len) => {
                let start = results.len() - len;
                let items: Vec<Expr> = results
                    .drain(start..)
                    .map(|arc| Arc::try_unwrap(arc).unwrap_or_else(|a| (*a).clone()))
                    .collect();
                results.push(Arc::new(Expr::lit(Literal::Array(items))));
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
                Expr::BVar(EBVar { idx }) => {
                    if *idx == cur_target {
                        let depth_offset = (cur_target - target) as isize;
                        results.push(Arc::new(shift(replacement, depth_offset, 0)));
                    } else if *idx > cur_target {
                        results.push(Arc::new(Expr::bvar(idx - 1)));
                    } else {
                        results.push(Arc::new(Expr::bvar(*idx)));
                    }
                }
                Expr::Sort(_) | Expr::FVar(_) | Expr::Const(_) | Expr::MVar(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::Lit(ELit {
                    lit: Literal::Array(items),
                }) => {
                    tasks.push(Task::BuildLitArray(items.len()));
                    for item in items.iter().rev() {
                        tasks.push(Task::Visit(item, cur_target));
                    }
                }
                Expr::Lit(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::App(app) => {
                    tasks.push(Task::BuildApp);
                    tasks.push(Task::Visit(&app.arg, cur_target));
                    tasks.push(Task::Visit(&app.f, cur_target));
                }
                Expr::Lam(lam) => {
                    tasks.push(Task::BuildLam(lam.var.clone()));
                    tasks.push(Task::Visit(&lam.body, cur_target + 1));
                    tasks.push(Task::Visit(&lam.t, cur_target));
                }
                Expr::Pi(pi) => {
                    tasks.push(Task::BuildPi(pi.var.clone()));
                    tasks.push(Task::Visit(&pi.body, cur_target + 1));
                    tasks.push(Task::Visit(&pi.t, cur_target));
                }
                Expr::Let(let_expr) => {
                    tasks.push(Task::BuildLet(let_expr.var.clone()));
                    tasks.push(Task::Visit(&let_expr.body, cur_target + 1));
                    tasks.push(Task::Visit(&let_expr.value, cur_target));
                    tasks.push(Task::Visit(&let_expr.t, cur_target));
                }
            },
            Task::BuildApp => {
                let arg = results.pop().unwrap();
                let fn_expr = results.pop().unwrap();
                results.push(Arc::new(Expr::app(fn_expr, arg)));
            }
            Task::BuildLam(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::lam(var, domain, body)));
            }
            Task::BuildPi(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::pi(var, domain, body)));
            }
            Task::BuildLet(var) => {
                let body = results.pop().unwrap();
                let value = results.pop().unwrap();
                let var_type = results.pop().unwrap();
                results.push(Arc::new(Expr::let_(var, var_type, value, body)));
            }
            Task::BuildLitArray(len) => {
                let start = results.len() - len;
                let items: Vec<Expr> = results
                    .drain(start..)
                    .map(|arc| Arc::try_unwrap(arc).unwrap_or_else(|a| (*a).clone()))
                    .collect();
                results.push(Arc::new(Expr::lit(Literal::Array(items))));
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
                Expr::FVar(EFVar { name: n }) => {
                    if n == name {
                        results.push(Arc::new(Expr::bvar(depth)));
                    } else {
                        results.push(Arc::new(cur.clone()));
                    }
                }
                Expr::BVar(_) | Expr::Sort(_) | Expr::Const(_) | Expr::MVar(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::Lit(ELit {
                    lit: Literal::Array(items),
                }) => {
                    tasks.push(Task::BuildLitArray(items.len()));
                    for item in items.iter().rev() {
                        tasks.push(Task::Visit(item, depth));
                    }
                }
                Expr::Lit(_) => {
                    results.push(Arc::new(cur.clone()));
                }
                Expr::App(app) => {
                    tasks.push(Task::BuildApp);
                    tasks.push(Task::Visit(&app.arg, depth));
                    tasks.push(Task::Visit(&app.f, depth));
                }
                Expr::Lam(lam) => {
                    tasks.push(Task::BuildLam(lam.var.clone()));
                    tasks.push(Task::Visit(&lam.body, depth + 1));
                    tasks.push(Task::Visit(&lam.t, depth));
                }
                Expr::Pi(pi) => {
                    tasks.push(Task::BuildPi(pi.var.clone()));
                    tasks.push(Task::Visit(&pi.body, depth + 1));
                    tasks.push(Task::Visit(&pi.t, depth));
                }
                Expr::Let(let_expr) => {
                    tasks.push(Task::BuildLet(let_expr.var.clone()));
                    tasks.push(Task::Visit(&let_expr.body, depth + 1));
                    tasks.push(Task::Visit(&let_expr.value, depth));
                    tasks.push(Task::Visit(&let_expr.t, depth));
                }
            },
            Task::BuildApp => {
                let arg = results.pop().unwrap();
                let fn_expr = results.pop().unwrap();
                results.push(Arc::new(Expr::app(fn_expr, arg)));
            }
            Task::BuildLam(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::lam(var, domain, body)));
            }
            Task::BuildPi(var) => {
                let body = results.pop().unwrap();
                let domain = results.pop().unwrap();
                results.push(Arc::new(Expr::pi(var, domain, body)));
            }
            Task::BuildLet(var) => {
                let body = results.pop().unwrap();
                let value = results.pop().unwrap();
                let var_type = results.pop().unwrap();
                results.push(Arc::new(Expr::let_(var, var_type, value, body)));
            }
            Task::BuildLitArray(len) => {
                let start = results.len() - len;
                let items: Vec<Expr> = results
                    .drain(start..)
                    .map(|arc| Arc::try_unwrap(arc).unwrap_or_else(|a| (*a).clone()))
                    .collect();
                results.push(Arc::new(Expr::lit(Literal::Array(items))));
            }
        }
    }

    let root = results.pop().unwrap();
    Arc::try_unwrap(root).unwrap_or_else(|arc| (*arc).clone())
}
