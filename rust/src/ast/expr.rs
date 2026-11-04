use pyo3::prelude::*;
use pyo3::types::PyAny;

use super::univ_level;

/// Expression
///
/// - Sort(u)                --- The type of types at universe level `u`.
/// - FVar(name)             --- Free variable with name `name`.
/// - BVar(idx)              --- Bound variable with de Bruijn index `idx`.
/// - Const(name, us)        --- Constant with name `name` and universe levels `us`.
/// - App(f, arg)            --- Application of function `f` to argument `arg`.
/// - Lam(var, T, body)      --- Lambda abstraction with variable `var`, type `T`, and body `body`.
/// - Pi(var, T, body)       --- Dependent function type with variable `var`, type `T`, and body `body`.
/// - Let(var, T, val, body) --- Let binding with variable `var`, type `T`, value `val`, and body `body`.
/// - MVar(id)               --- Metavariable with identifier `id`.
#[derive(Clone)]
pub enum Expr {
    /// `Sort u` is the type of types at universe level `u`.
    Sort(univ_level::UnivLevel),
    FVar(String),
    BVar(usize),
    Const(String, Vec<univ_level::UnivLevel>),
    App(Box<Expr>, Vec<Expr>),
    Lam(String, Box<Expr>, Box<Expr>),
    Pi(String, Box<Expr>, Box<Expr>),
    Let(String, Box<Expr>, Box<Expr>, Box<Expr>),
    MVar(String),
}

#[pyclass(name = "ESort")]
struct PyESort {
    level: univ_level::UnivLevel,
}

#[pymethods]
impl PyESort {
    #[getter]
    fn level(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        univ_level::to_pyresult(py, self.level.clone())
    }
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyESort>()?;

    Ok(())
}
