use pyo3::prelude::*;
use pyo3::types::PyAny;

use super::univ_level;

/// Expression
///
/// - Sort(u)                  --- The type of types at universe level `u`.
/// - FVar(name)               --- Free variable with name `name`.
/// - BVar(idx)                --- Bound variable with de Bruijn index `idx`.
/// - Const(name, levels)      --- Constant with name `name` and universe levels `us`.
/// - App(f, arg)              --- Application of function `f` to argument `arg`.
/// - Lam(var, t, body)        --- Lambda abstraction with variable `var`, type `T`, and body `body`.
/// - Pi(var, t, body)         --- Dependent function type with variable `var`, type `T`, and body `body`.
/// - Let(var, t, value, body) --- Let binding with variable `var`, type `T`, value `val`, and body `body`.
/// - MVar(id)                 --- Metavariable with identifier `id`.
#[derive(Clone)]
pub enum Expr {
    Sort(univ_level::UnivLevel),
    FVar(String),
    BVar(usize),
    Const(String, Vec<univ_level::UnivLevel>),
    App(Box<Expr>, Box<Expr>),
    Lam(String, Box<Expr>, Box<Expr>),
    Pi(String, Box<Expr>, Box<Expr>),
    Let(String, Box<Expr>, Box<Expr>, Box<Expr>),
    MVar(String),
}

#[pyclass(name = "ESort")]
struct PySort {
    level: univ_level::UnivLevel,
}

#[pymethods]
impl PySort {
    #[getter]
    fn level(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        univ_level::to_pyresult(py, self.level.clone())
    }
}

#[pyclass(name = "EFVar")]
struct PyFVar {
    #[pyo3(get)]
    name: String,
}

#[pyclass(name = "EBVar")]
struct PyBVar {
    #[pyo3(get)]
    idx: usize,
}

#[pyclass(name = "EConst")]
struct PyConst {
    #[pyo3(get)]
    name: String,
    levels: Vec<univ_level::UnivLevel>,
}

#[pymethods]
impl PyConst {
    #[getter]
    fn levels(&self, py: Python<'_>) -> PyResult<Vec<Py<PyAny>>> {
        self.levels
            .iter()
            .map(|level| univ_level::to_pyresult(py, level.clone()))
            .collect()
    }
}

#[pyclass(name = "EApp")]
struct PyApp {
    f: Box<Expr>,
    arg: Box<Expr>,
}

#[pymethods]
impl PyApp {
    #[getter]
    fn f(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.f.clone())
    }

    #[getter]
    fn arg(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.arg.clone())
    }
}

#[pyclass(name = "ELam")]
struct PyLam {
    #[pyo3(get)]
    var: String,
    t: Box<Expr>,
    body: Box<Expr>,
}

#[pymethods]
impl PyLam {
    #[getter]
    fn t(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.t.clone())
    }

    #[getter]
    fn body(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.body.clone())
    }
}

#[pyclass(name = "EPi")]
struct PyPi {
    #[pyo3(get)]
    var: String,
    t: Box<Expr>,
    body: Box<Expr>,
}

#[pymethods]
impl PyPi {
    #[getter]
    fn t(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.t.clone())
    }

    #[getter]
    fn body(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.body.clone())
    }
}

#[pyclass(name = "ELet")]
struct PyLet {
    #[pyo3(get)]
    var: String,
    t: Box<Expr>,
    value: Box<Expr>,
    body: Box<Expr>,
}

#[pymethods]
impl PyLet {
    #[getter]
    fn t(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.t.clone())
    }

    #[getter]
    fn value(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.value.clone())
    }

    #[getter]
    fn body(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.body.clone())
    }
}

#[pyclass(name = "EMVar")]
struct PyMVar {
    #[pyo3(get)]
    id: String,
}

pub fn to_pyresult(py: Python<'_>, expr: Expr) -> PyResult<Py<PyAny>> {
    match expr {
        Expr::Sort(level) => Ok(Bound::new(py, PySort { level })?.into_any().unbind()),
        Expr::FVar(name) => Ok(Bound::new(py, PyFVar { name })?.into_any().unbind()),
        Expr::BVar(idx) => Ok(Bound::new(py, PyBVar { idx })?.into_any().unbind()),
        Expr::Const(name, levels) => Ok(Bound::new(py, PyConst { name, levels })?
            .into_any()
            .unbind()),
        Expr::App(f, arg) => Ok(Bound::new(py, PyApp { f, arg })?.into_any().unbind()),
        Expr::Lam(var, t, body) => Ok(Bound::new(py, PyLam { var, t, body })?.into_any().unbind()),
        Expr::Pi(var, t, body) => Ok(Bound::new(py, PyPi { var, t, body })?.into_any().unbind()),
        Expr::Let(var, t, value, body) => Ok(Bound::new(
            py,
            PyLet {
                var,
                t,
                value,
                body,
            },
        )?
        .into_any()
        .unbind()),
        Expr::MVar(id) => Ok(Bound::new(py, PyMVar { id })?.into_any().unbind()),
    }
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySort>()?;
    m.add_class::<PyFVar>()?;
    m.add_class::<PyBVar>()?;
    m.add_class::<PyConst>()?;
    m.add_class::<PyApp>()?;
    m.add_class::<PyLam>()?;
    m.add_class::<PyPi>()?;
    m.add_class::<PyLet>()?;
    m.add_class::<PyMVar>()?;

    Ok(())
}
