use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use super::univ_level;

#[derive(Clone, Debug)]
pub enum Literal {
    Nat(u64),
    Float(f64),
    String(String),
    Array(Vec<Expr>),
}

impl<'py> IntoPyObject<'py> for Literal {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            Literal::Nat(val) => Ok(val.into_pyobject(py)?.into_any()),
            Literal::Float(val) => Ok(val.into_pyobject(py)?.into_any()),
            Literal::String(val) => Ok(val.into_pyobject(py)?.into_any()),
            Literal::Array(vals) => Ok(vals.into_pyobject(py)?.into_any()),
        }
    }
}

impl<'a, 'py> FromPyObject<'a, 'py> for Literal {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        if let Ok(val) = ob.extract::<u64>() {
            Ok(Literal::Nat(val))
        } else if let Ok(val) = ob.extract::<f64>() {
            Ok(Literal::Float(val))
        } else if let Ok(val) = ob.extract::<String>() {
            Ok(Literal::String(val))
        } else if let Ok(vals) = ob.extract::<Vec<Expr>>() {
            Ok(Literal::Array(vals))
        } else {
            Err(PyTypeError::new_err(
                "Expected int, float, str, or list[Expr] for Literal",
            ))
        }
    }
}

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
/// - Lit(lit)                 --- Literal value `lit`.
/// - MVar(id)                 --- Metavariable with identifier `id`.
#[derive(Clone, Debug)]
pub enum Expr {
    Sort(univ_level::UnivLevel),
    FVar(String),
    BVar(usize),
    Const(String, Vec<univ_level::UnivLevel>),
    App(Box<Expr>, Box<Expr>),
    Lam(String, Box<Expr>, Box<Expr>),
    Pi(String, Box<Expr>, Box<Expr>),
    Let(String, Box<Expr>, Box<Expr>, Box<Expr>),
    Lit(Literal),
    MVar(String),
}

#[pyclass(name = "ESort")]
struct PySort {
    #[pyo3(get)]
    level: univ_level::UnivLevel,
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
    #[pyo3(get)]
    levels: Vec<univ_level::UnivLevel>,
}

#[pyclass(name = "EApp")]
struct PyApp {
    #[pyo3(get)]
    f: Expr,
    #[pyo3(get)]
    arg: Expr,
}

#[pyclass(name = "ELam")]
struct PyLam {
    #[pyo3(get)]
    var: String,
    #[pyo3(get)]
    t: Expr,
    #[pyo3(get)]
    body: Expr,
}

#[pyclass(name = "EPi")]
struct PyPi {
    #[pyo3(get)]
    var: String,
    #[pyo3(get)]
    t: Expr,
    #[pyo3(get)]
    body: Expr,
}

#[pyclass(name = "ELet")]
struct PyLet {
    #[pyo3(get)]
    var: String,
    #[pyo3(get)]
    t: Expr,
    #[pyo3(get)]
    value: Expr,
    #[pyo3(get)]
    body: Expr,
}

#[pyclass(name = "ELit")]
struct PyLit {
    #[pyo3(get)]
    lit: Literal,
}

#[pyclass(name = "EMVar")]
struct PyMVar {
    #[pyo3(get)]
    id: String,
}

impl<'py> IntoPyObject<'py> for Expr {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            Expr::Sort(level) => Ok(Bound::new(py, PySort { level })?.into_any()),
            Expr::FVar(name) => Ok(Bound::new(py, PyFVar { name })?.into_any()),
            Expr::BVar(idx) => Ok(Bound::new(py, PyBVar { idx })?.into_any()),
            Expr::Const(name, levels) => Ok(Bound::new(py, PyConst { name, levels })?.into_any()),
            Expr::App(f, arg) => Ok(Bound::new(
                py,
                PyApp {
                    f: *f,
                    arg: *arg,
                },
            )?
            .into_any()),
            Expr::Lam(var, t, body) => Ok(Bound::new(
                py,
                PyLam {
                    var,
                    t: *t,
                    body: *body,
                },
            )?
            .into_any()),
            Expr::Pi(var, t, body) => Ok(Bound::new(
                py,
                PyPi {
                    var,
                    t: *t,
                    body: *body,
                },
            )?
            .into_any()),
            Expr::Let(var, t, value, body) => Ok(Bound::new(
                py,
                PyLet {
                    var,
                    t: *t,
                    value: *value,
                    body: *body,
                },
            )?
            .into_any()),
            Expr::Lit(lit) => Ok(Bound::new(py, PyLit { lit })?.into_any()),
            Expr::MVar(id) => Ok(Bound::new(py, PyMVar { id })?.into_any()),
        }
    }
}

impl<'a, 'py> FromPyObject<'a, 'py> for Expr {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        if let Ok(s) = ob.extract::<PyRef<'_, PySort>>() {
            Ok(Expr::Sort(s.level.clone()))
        } else if let Ok(v) = ob.extract::<PyRef<'_, PyFVar>>() {
            Ok(Expr::FVar(v.name.clone()))
        } else if let Ok(v) = ob.extract::<PyRef<'_, PyBVar>>() {
            Ok(Expr::BVar(v.idx))
        } else if let Ok(c) = ob.extract::<PyRef<'_, PyConst>>() {
            Ok(Expr::Const(c.name.clone(), c.levels.clone()))
        } else if let Ok(a) = ob.extract::<PyRef<'_, PyApp>>() {
            Ok(Expr::App(
                Box::new(a.f.clone()),
                Box::new(a.arg.clone()),
            ))
        } else if let Ok(l) = ob.extract::<PyRef<'_, PyLam>>() {
            Ok(Expr::Lam(
                l.var.clone(),
                Box::new(l.t.clone()),
                Box::new(l.body.clone()),
            ))
        } else if let Ok(p) = ob.extract::<PyRef<'_, PyPi>>() {
            Ok(Expr::Pi(
                p.var.clone(),
                Box::new(p.t.clone()),
                Box::new(p.body.clone()),
            ))
        } else if let Ok(l) = ob.extract::<PyRef<'_, PyLet>>() {
            Ok(Expr::Let(
                l.var.clone(),
                Box::new(l.t.clone()),
                Box::new(l.value.clone()),
                Box::new(l.body.clone()),
            ))
        } else if let Ok(l) = ob.extract::<PyRef<'_, PyLit>>() {
            Ok(Expr::Lit(l.lit.clone()))
        } else if let Ok(m) = ob.extract::<PyRef<'_, PyMVar>>() {
            Ok(Expr::MVar(m.id.clone()))
        } else {
            Err(PyTypeError::new_err("Expected an Expr instance"))
        }
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
    m.add_class::<PyLit>()?;
    m.add_class::<PyMVar>()?;
    Ok(())
}