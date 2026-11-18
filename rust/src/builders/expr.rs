/// Builder functions for constructing AST expressions.
///
/// This module provides ergonomic builder functions to construct expressions,
/// drawing inspiration from the Python implementations in ast/ops.py.
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use crate::ast::expr::Expr;
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
    F: Fn(String, Box<Expr>, Box<Expr>) -> Expr,
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
        result = constructor(var_name, Box::new(domain), Box::new(abstracted));
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
        Expr::App(Box::new(acc), Box::new(arg.0))
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
        Box::new(var_type.0),
        Box::new(value.0),
        Box::new(abstracted),
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

/// Abstract a free variable name to a de Bruijn index.
///
/// Recursively traverses the expression, replacing all occurrences of the named
/// free variable with de Bruijn indices relative to the binding depth.
pub fn abstract_name_to_bvar(expr: &Expr, name: &str) -> Expr {
    fn go(expr: &Expr, name: &str, depth: usize) -> Expr {
        match expr {
            Expr::FVar(n) => {
                if n == name {
                    Expr::BVar(depth)
                } else {
                    expr.clone()
                }
            }
            Expr::BVar(_) | Expr::Sort(_) | Expr::Const(_, _) | Expr::Lit(_) | Expr::MVar(_) => {
                expr.clone()
            }
            Expr::App(fn_expr, arg) => {
                Expr::App(Box::new(go(fn_expr, name, depth)), Box::new(go(arg, name, depth)))
            }
            Expr::Lam(var, domain, body) => Expr::Lam(
                var.clone(),
                Box::new(go(domain, name, depth)),
                Box::new(go(body, name, depth + 1)),
            ),
            Expr::Let(var, var_type, value, body) => Expr::Let(
                var.clone(),
                Box::new(go(var_type, name, depth)),
                Box::new(go(value, name, depth)),
                Box::new(go(body, name, depth + 1)),
            ),
            Expr::Pi(var, domain, body) => Expr::Pi(
                var.clone(),
                Box::new(go(domain, name, depth)),
                Box::new(go(body, name, depth + 1)),
            ),
        }
    }
    go(expr, name, 0)
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