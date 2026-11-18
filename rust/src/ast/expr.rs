use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBool, PyFloat, PyInt, PyList, PyString};
use super::univ_level;

#[derive(Clone, Debug)]
pub enum Literal {
    Nat(u64),
    Float(f64),
    String(String),
    Array(Vec<Expr>),
}

impl<'a, 'py> FromPyObject<'a, 'py> for Literal {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> PyResult<Self> {
        if ob.is_instance_of::<PyBool>() {
            Err(PyTypeError::new_err(
                "Expected int (non-negative), float, str, or list for Literal, got bool",
            ))
        } else if ob.is_instance_of::<PyInt>() {
            let val = ob.extract::<u64>().map_err(|_| {
                PyValueError::new_err(
                    "Natural number literal must be a non-negative integer within u64 range.",
                )
            })?;
            Ok(Literal::Nat(val))
        } else if ob.is_instance_of::<PyFloat>() {
            Ok(Literal::Float(ob.extract::<f64>()?))
        } else if ob.is_instance_of::<PyString>() {
            Ok(Literal::String(ob.extract::<String>()?))
        } else if ob.is_instance_of::<PyList>() {
            Ok(Literal::Array(ob.extract::<Vec<Expr>>()?))
        } else {
            let type_name = ob.get_type().name()?;
            Err(PyTypeError::new_err(format!(
                "Expected int (non-negative), float, str, or list for Literal, got {type_name}"
            )))
        }
    }
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

#[pyclass(name = "ESort", get_all)]
struct PySort {
    level: univ_level::UnivLevel,
}

#[pyclass(name = "EFVar", get_all)]
struct PyFVar {
    name: String,
}

#[pyclass(name = "EBVar", get_all)]
struct PyBVar {
    idx: usize,
}

#[pyclass(name = "EConst", get_all)]
struct PyConst {
    name: String,
    levels: Vec<univ_level::UnivLevel>,
}

#[pyclass(name = "EApp", get_all)]
struct PyApp {
    f: Expr,
    arg: Expr,
}

#[pyclass(name = "ELam", get_all)]
struct PyLam {
    var: String,
    t: Expr,
    body: Expr,
}

#[pyclass(name = "EPi", get_all)]
struct PyPi {
    var: String,
    t: Expr,
    body: Expr,
}

#[pyclass(name = "ELet", get_all)]
struct PyLet {
    var: String,
    t: Expr,
    value: Expr,
    body: Expr,
}

#[pyclass(name = "ELit", get_all)]
struct PyLit {
    lit: Literal,
}

#[pyclass(name = "EMVar", get_all)]
struct PyMVar {
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
            Expr::Const(name, levels) => {
                Ok(Bound::new(py, PyConst { name, levels })?.into_any())
            }
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

#[derive(FromPyObject)]
enum PyExpr<'py> {
    Sort(PyRef<'py, PySort>),
    FVar(PyRef<'py, PyFVar>),
    BVar(PyRef<'py, PyBVar>),
    Const(PyRef<'py, PyConst>),
    App(PyRef<'py, PyApp>),
    Lam(PyRef<'py, PyLam>),
    Pi(PyRef<'py, PyPi>),
    Let(PyRef<'py, PyLet>),
    Lit(PyRef<'py, PyLit>),
    MVar(PyRef<'py, PyMVar>),
}

impl<'a, 'py> FromPyObject<'a, 'py> for Expr {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        match ob.extract::<PyExpr<'py>>()? {
            PyExpr::Sort(s) => Ok(Expr::Sort(s.level.clone())),
            PyExpr::FVar(v) => Ok(Expr::FVar(v.name.clone())),
            PyExpr::BVar(b) => Ok(Expr::BVar(b.idx)),
            PyExpr::Const(c) => Ok(Expr::Const(c.name.clone(), c.levels.clone())),
            PyExpr::App(a) => Ok(Expr::App(Box::new(a.f.clone()), Box::new(a.arg.clone()))),
            PyExpr::Lam(l) => Ok(Expr::Lam(
                l.var.clone(),
                Box::new(l.t.clone()),
                Box::new(l.body.clone()),
            )),
            PyExpr::Pi(p) => Ok(Expr::Pi(
                p.var.clone(),
                Box::new(p.t.clone()),
                Box::new(p.body.clone()),
            )),
            PyExpr::Let(l) => Ok(Expr::Let(
                l.var.clone(),
                Box::new(l.t.clone()),
                Box::new(l.value.clone()),
                Box::new(l.body.clone()),
            )),
            PyExpr::Lit(l) => Ok(Expr::Lit(l.lit.clone())),
            PyExpr::MVar(m) => Ok(Expr::MVar(m.id.clone())),
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
