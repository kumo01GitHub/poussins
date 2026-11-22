use std::sync::Arc;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use crate::ast::expr::Expr;
use crate::ast::ops::bind;
use crate::builders::univ_level::{try_build_univ_level, UnivLevelInput};

/// Input wrapper accepting either an `Expr` or a `str` (coerced into `Expr::FVar`).
pub struct ExprInput(pub Expr);

impl<'a, 'py> FromPyObject<'a, 'py> for ExprInput {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> PyResult<Self> {
        if let Ok(s) = ob.extract::<String>() {
            Ok(Self(Expr::fvar(s)))
        } else {
            ob.extract::<Expr>().map(Self)
        }
    }
}

fn fold_binders<F>(
    binders: impl IntoIterator<Item = (String, ExprInput)>,
    body: ExprInput,
    constructor: F,
) -> Expr
where
    F: Fn(String, Arc<Expr>, Arc<Expr>) -> Expr,
{
    let mut result = body.0;
    let binders_vec: Vec<(String, Expr)> = binders
        .into_iter()
        .map(|(name, ty)| (name, ty.0))
        .collect();
    for (var_name, domain) in binders_vec.into_iter().rev() {
        let abstracted = if var_name == "_" {
            result
        } else {
            bind(&result, &var_name)
        };
        result = constructor(var_name, Arc::new(domain), Arc::new(abstracted));
    }
    result
}

/// Build a Sort expression from a universe level.
#[pyfunction]
pub fn sort(level: UnivLevelInput) -> PyResult<Expr> {
    let lvl = try_build_univ_level(level)?;
    Ok(Expr::sort(lvl))
}

/// Build a free variable expression from a name.
#[pyfunction]
pub fn free_var(name: String) -> Expr {
    Expr::fvar(name)
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
        Expr::app(Arc::new(acc), Arc::new(arg.0))
    })
}

/// Build nested lambda abstractions from binders and a body.
#[pyfunction]
pub fn lam(binders: Vec<(String, ExprInput)>, body: ExprInput) -> Expr {
    fold_binders(binders, body, Expr::lam)
}

/// Build a let-binding expression with a single variable.
#[pyfunction]
pub fn let_(var_name: String, var_type: ExprInput, value: ExprInput, body: ExprInput) -> Expr {
    let abstracted = if var_name == "_" {
        body.0
    } else {
        bind(&body.0, &var_name)
    };
    Expr::let_(
        var_name,
        Arc::new(var_type.0),
        Arc::new(value.0),
        Arc::new(abstracted),
    )
}

/// Build nested Pi (dependent function) types from binders and a body.
#[pyfunction]
pub fn pi(binders: Vec<(String, ExprInput)>, body: ExprInput) -> Expr {
    fold_binders(binders, body, Expr::pi)
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
    Ok(Expr::const_(decl_name, levels))
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
