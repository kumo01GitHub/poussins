/// Builder functions for constructing AST expressions.
///
/// This module provides ergonomic builder functions to construct expressions,
/// drawing inspiration from the Python implementations in ast/ops.py.

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyTuple};

use crate::ast::expr::{to_pyresult, Expr, Literal};
use crate::builders::univ_level::extract_univ_level;

fn extract_expr(obj: &Bound<'_, PyAny>) -> PyResult<Expr> {
    let type_name = obj.get_type().name()?;
    let type_str = type_name.to_str()?;
    match type_str {
        "ESort" => {
            let level = obj.getattr("level")?;
            Ok(Expr::Sort(extract_univ_level(&level)?))
        }
        "EFVar" => {
            let name: String = obj.getattr("name")?.extract()?;
            Ok(Expr::FVar(name))
        }
        "EBVar" => {
            let idx: usize = obj.getattr("idx")?.extract()?;
            Ok(Expr::BVar(idx))
        }
        "EConst" => {
            let name: String = obj.getattr("name")?.extract()?;
            let levels_obj = obj.getattr("levels")?;
            let mut levels = Vec::new();
            for lvl in levels_obj.try_iter()? {
                levels.push(extract_univ_level(&lvl?)?);
            }
            Ok(Expr::Const(name, levels))
        }
        "EApp" => {
            let f_obj = obj.getattr("f")?;
            let arg_obj = obj.getattr("arg")?;
            Ok(Expr::App(
                Box::new(extract_expr(&f_obj)?),
                Box::new(extract_expr(&arg_obj)?),
            ))
        }
        "ELam" => {
            let var: String = obj.getattr("var")?.extract()?;
            let t_obj = obj.getattr("t")?;
            let body_obj = obj.getattr("body")?;
            Ok(Expr::Lam(
                var,
                Box::new(extract_expr(&t_obj)?),
                Box::new(extract_expr(&body_obj)?),
            ))
        }
        "EPi" => {
            let var: String = obj.getattr("var")?.extract()?;
            let t_obj = obj.getattr("t")?;
            let body_obj = obj.getattr("body")?;
            Ok(Expr::Pi(
                var,
                Box::new(extract_expr(&t_obj)?),
                Box::new(extract_expr(&body_obj)?),
            ))
        }
        "ELet" => {
            let var: String = obj.getattr("var")?.extract()?;
            let t_obj = obj.getattr("t")?;
            let val_obj = obj.getattr("value")?;
            let body_obj = obj.getattr("body")?;
            Ok(Expr::Let(
                var,
                Box::new(extract_expr(&t_obj)?),
                Box::new(extract_expr(&val_obj)?),
                Box::new(extract_expr(&body_obj)?),
            ))
        }
        "ELit" => {
            let lit_obj = obj.getattr("lit")?;
            if let Ok(n) = lit_obj.extract::<u64>() {
                Ok(Expr::Lit(Literal::Nat(n)))
            } else if let Ok(f) = lit_obj.extract::<f64>() {
                Ok(Expr::Lit(Literal::Float(f)))
            } else if let Ok(s) = lit_obj.extract::<String>() {
                Ok(Expr::Lit(Literal::String(s)))
            } else {
                let mut list = Vec::new();
                for item in lit_obj.try_iter()? {
                    list.push(extract_expr(&item?)?);
                }
                Ok(Expr::Lit(Literal::Array(list)))
            }
        }
        "EMVar" => {
            let id: String = obj.getattr("id")?.extract()?;
            Ok(Expr::MVar(id))
        }
        _ => Err(PyTypeError::new_err(format!(
            "Expected Expr, got {}",
            type_str
        ))),
    }
}

fn extract_expr_or_var(obj: &Bound<'_, PyAny>) -> PyResult<Expr> {
    if let Ok(s) = obj.extract::<String>() {
        Ok(Expr::FVar(s))
    } else {
        extract_expr(obj)
    }
}

/// Build a Sort expression from a universe level.
#[pyfunction]
#[pyo3(signature = (level))]
pub fn sort(py: Python<'_>, level: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let lvl = extract_univ_level(level)?;
    to_pyresult(py, Expr::Sort(lvl))
}

/// Build a free variable expression from a name.
#[pyfunction]
#[pyo3(signature = (name))]
pub fn var(py: Python<'_>, name: String) -> PyResult<Py<PyAny>> {
    to_pyresult(py, Expr::FVar(name))
}

/// Explicit alias for `var`, emphasizing that this creates a free variable.
#[pyfunction]
#[pyo3(signature = (name))]
pub fn free_var(py: Python<'_>, name: String) -> PyResult<Py<PyAny>> {
    var(py, name)
}

/// Build a left-associated application chain from a head function and arguments.
#[pyfunction]
#[pyo3(signature = (r#fn, *args))]
pub fn app(
    py: Python<'_>,
    r#fn: &Bound<'_, PyAny>,
    args: &Bound<'_, PyTuple>,
) -> PyResult<Py<PyAny>> {
    let mut result = extract_expr_or_var(r#fn)?;
    for arg in args {
        let arg_expr = extract_expr_or_var(&arg)?;
        result = Expr::App(Box::new(result), Box::new(arg_expr));
    }
    to_pyresult(py, result)
}

/// Build nested lambda abstractions from binders and a body.
#[pyfunction]
#[pyo3(signature = (binders, body))]
pub fn lam(
    py: Python<'_>,
    binders: &Bound<'_, PyAny>,
    body: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    let mut binders_vec: Vec<(String, Expr)> = Vec::new();
    for item in binders.try_iter()? {
        let item = item?;
        let (var_name, dom_any): (String, Bound<'_, PyAny>) = item.extract()?;
        let dom = extract_expr_or_var(&dom_any)?;
        binders_vec.push((var_name, dom));
    }

    let mut result = extract_expr_or_var(body)?;
    for (var_name, domain) in binders_vec.into_iter().rev() {
        let abstracted = if var_name == "_" {
            result
        } else {
            abstract_name_to_bvar(&result, &var_name)
        };
        result = Expr::Lam(var_name, Box::new(domain), Box::new(abstracted));
    }

    to_pyresult(py, result)
}

/// Build a let-binding expression with a single variable.
#[pyfunction]
#[pyo3(signature = (var_name, var_type, value, body))]
pub fn let_(
    py: Python<'_>,
    var_name: String,
    var_type: &Bound<'_, PyAny>,
    value: &Bound<'_, PyAny>,
    body: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    let var_type_expr = extract_expr_or_var(var_type)?;
    let value_expr = extract_expr_or_var(value)?;
    let body_expr = extract_expr_or_var(body)?;

    let abstracted = if var_name == "_" {
        body_expr
    } else {
        abstract_name_to_bvar(&body_expr, &var_name)
    };

    let result = Expr::Let(
        var_name,
        Box::new(var_type_expr),
        Box::new(value_expr),
        Box::new(abstracted),
    );

    to_pyresult(py, result)
}

/// Build nested Pi (dependent function) types from binders and a body.
#[pyfunction]
#[pyo3(signature = (binders, body))]
pub fn pi(
    py: Python<'_>,
    binders: &Bound<'_, PyAny>,
    body: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    let mut binders_vec: Vec<(String, Expr)> = Vec::new();
    for item in binders.try_iter()? {
        let item = item?;
        let (var_name, dom_any): (String, Bound<'_, PyAny>) = item.extract()?;
        let dom = extract_expr_or_var(&dom_any)?;
        binders_vec.push((var_name, dom));
    }

    let mut result = extract_expr_or_var(body)?;
    for (var_name, domain) in binders_vec.into_iter().rev() {
        let abstracted = if var_name == "_" {
            result
        } else {
            abstract_name_to_bvar(&result, &var_name)
        };
        result = Expr::Pi(var_name, Box::new(domain), Box::new(abstracted));
    }

    to_pyresult(py, result)
}

/// Create an `Expr::Const` expression for a declaration in the environment.
#[pyfunction]
#[pyo3(signature = (env, name))]
pub fn const_(py: Python<'_>, env: &Bound<'_, PyAny>, name: &str) -> PyResult<Py<PyAny>> {
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
        let param = param?;
        levels.push(extract_univ_level(&param)?);
    }

    let expr = Expr::Const(decl_name, levels);
    to_pyresult(py, expr)
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
            Expr::Lam(var, domain, body) => {
                Expr::Lam(
                    var.clone(),
                    Box::new(go(domain, name, depth)),
                    Box::new(go(body, name, depth + 1)),
                )
            }
            Expr::Let(var, var_type, value, body) => {
                Expr::Let(
                    var.clone(),
                    Box::new(go(var_type, name, depth)),
                    Box::new(go(value, name, depth)),
                    Box::new(go(body, name, depth + 1)),
                )
            }
            Expr::Pi(var, domain, body) => {
                Expr::Pi(
                    var.clone(),
                    Box::new(go(domain, name, depth)),
                    Box::new(go(body, name, depth + 1)),
                )
            }
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
