/// Builder functions for constructing AST expressions.
///
/// This module provides ergonomic builder functions to construct expressions,
/// drawing inspiration from the Python implementations in ast/ops.py.
use std::sync::Arc;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use crate::ast::expr::{Expr, Literal};
use crate::builders::univ_level::{try_build_univ_level, UnivLevelInput};

/// Input wrapper accepting either an `Expr` or a `str` (coerced into `Expr::FVar`).
pub struct ExprInput(pub Expr);

impl<'a, 'py> FromPyObject<'a, 'py> for ExprInput {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> PyResult<Self> {
        if let Ok(s) = ob.extract::<String>() {
            Ok(Self(Expr::FVar(s)))
        } else {
            ob.extract::<Expr>().map(Self)
        }
    }
}

fn fold_binders<F>(binders: &Bound<'_, PyAny>, body: ExprInput, constructor: F) -> PyResult<Expr>
where
    F: Fn(String, Arc<Expr>, Arc<Expr>) -> Expr,
{
    let mut binders_vec: Vec<(String, Expr)> = Vec::new();
    for item in binders.try_iter()? {
        let (var_name, dom): (String, ExprInput) = item?.extract()?;
        binders_vec.push((var_name, dom.0));
    }

    let mut result = body.0;
    for (var_name, domain) in binders_vec.into_iter().rev() {
        let abstracted = if var_name == "_" {
            result
        } else {
            abstract_name_to_bvar(&result, &var_name)
        };
        result = constructor(var_name, Arc::new(domain), Arc::new(abstracted));
    }
    Ok(result)
}

/// Build a Sort expression from a universe level.
#[pyfunction]
pub fn sort(level: UnivLevelInput) -> PyResult<Expr> {
    let lvl = try_build_univ_level(level)?;
    Ok(Expr::Sort(lvl))
}

/// Build a free variable expression from a name.
#[pyfunction]
pub fn free_var(name: String) -> Expr {
    Expr::FVar(name)
}

/// Shorthand alias for `free_var`.
#[pyfunction]
pub fn var(name: String) -> Expr {
    free_var(name)
}

/// Build a left-associated application chain from a head function and arguments.
#[pyfunction]
#[pyo3(signature = (r#fn, *args))]
pub fn app(r#fn: ExprInput, args: Vec<ExprInput>) -> Expr {
    args.into_iter().fold(r#fn.0, |acc, arg| {
        Expr::App(Arc::new(acc), Arc::new(arg.0))
    })
}

/// Build nested lambda abstractions from binders and a body.
#[pyfunction]
pub fn lam(binders: &Bound<'_, PyAny>, body: ExprInput) -> PyResult<Expr> {
    fold_binders(binders, body, Expr::Lam)
}

/// Build a let-binding expression with a single variable.
#[pyfunction]
pub fn let_(var_name: String, var_type: ExprInput, value: ExprInput, body: ExprInput) -> Expr {
    let abstracted = if var_name == "_" {
        body.0
    } else {
        abstract_name_to_bvar(&body.0, &var_name)
    };
    Expr::Let(
        var_name,
        Arc::new(var_type.0),
        Arc::new(value.0),
        Arc::new(abstracted),
    )
}

/// Build nested Pi (dependent function) types from binders and a body.
#[pyfunction]
pub fn pi(binders: &Bound<'_, PyAny>, body: ExprInput) -> PyResult<Expr> {
    fold_binders(binders, body, Expr::Pi)
}

/// Create an `Expr::Const` expression for a declaration in the environment.
#[pyfunction]
pub fn const_(env: &Bound<'_, PyAny>, name: &str) -> PyResult<Expr> {
    let decl = env.call_method1("get", (name,))?;
    if decl.is_none() {
        return Err(PyValueError::new_err(format!(
            "Declaration with name '{name}' does not exist in the environment."
        )));
    }

    let decl_name: String = if let Ok(n) = decl.getattr("name") {
        n.extract()?
    } else {
        name.to_string()
    };

    let level_params = decl.getattr("level_params")?;
    let mut levels = Vec::new();
    for param in level_params.try_iter()? {
        let input: UnivLevelInput = param?.extract()?;
        levels.push(try_build_univ_level(input)?);
    }

    Ok(Expr::Const(decl_name, levels))
}

/// Abstract a free variable name to a de Bruijn index iteratively (stack-safe).
///
/// Traverses the expression using an explicit stack, replacing all occurrences
/// of the named free variable with de Bruijn indices relative to the binding depth.
pub fn abstract_name_to_bvar(expr: &Expr, name: &str) -> Expr {
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

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sort, m)?)?;
    m.add_function(wrap_pyfunction!(var, m)?)?;
    m.add_function(wrap_pyfunction!(free_var, m)?)?;
    m.add_function(wrap_pyfunction!(app, m)?)?;
    m.add_function(wrap_pyfunction!(lam, m)?)?;
    m.add_function(wrap_pyfunction!(let_, m)?)?;
    m.add_function(wrap_pyfunction!(pi, m)?)?;
    m.add_function(wrap_pyfunction!(const_, m)?)?;
    Ok(())
}
