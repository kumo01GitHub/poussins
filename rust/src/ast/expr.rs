use std::sync::Arc;

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

impl<'py> IntoPyObject<'py> for Literal {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            Literal::Nat(val) => Ok(val.into_pyobject(py)?.into_any()),
            Literal::Float(val) => Ok(val.into_pyobject(py)?.into_any()),
            Literal::String(val) => Ok(val.into_pyobject(py)?.into_any()),
            Literal::Array(vals) => {
                let mut py_vals = Vec::with_capacity(vals.len());
                for v in vals {
                    py_vals.push(v.into_pyobject(py)?);
                }
                Ok(PyList::new(py, py_vals)?.into_any())
            }
        }
    }
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
        } else if let Ok(list) = ob.cast::<PyList>() {
            let mut items = Vec::with_capacity(list.len());
            for item in list.iter() {
                items.push(item.extract::<Expr>()?);
            }
            Ok(Literal::Array(items))
        } else {
            let type_name = ob.get_type().name()?;
            Err(PyTypeError::new_err(format!(
                "Expected int (non-negative), float, str, or list for Literal, got {type_name}"
            )))
        }
    }
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct ESort {
    #[pyo3(get)]
    pub level: univ_level::UnivLevel,
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct EFVar {
    #[pyo3(get)]
    pub name: String,
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct EBVar {
    #[pyo3(get)]
    pub idx: usize,
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct EConst {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub levels: Vec<univ_level::UnivLevel>,
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct EApp {
    pub f: Arc<Expr>,
    pub arg: Arc<Expr>,
}

#[pymethods]
impl EApp {
    #[getter]
    fn f(&self) -> Expr {
        (*self.f).clone()
    }

    #[getter]
    fn arg(&self) -> Expr {
        (*self.arg).clone()
    }
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct ELam {
    #[pyo3(get)]
    pub var: String,
    pub t: Arc<Expr>,
    pub body: Arc<Expr>,
}

#[pymethods]
impl ELam {
    #[getter]
    fn t(&self) -> Expr {
        (*self.t).clone()
    }

    #[getter]
    fn body(&self) -> Expr {
        (*self.body).clone()
    }
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct EPi {
    #[pyo3(get)]
    pub var: String,
    pub t: Arc<Expr>,
    pub body: Arc<Expr>,
}

#[pymethods]
impl EPi {
    #[getter]
    fn t(&self) -> Expr {
        (*self.t).clone()
    }

    #[getter]
    fn body(&self) -> Expr {
        (*self.body).clone()
    }
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct ELet {
    #[pyo3(get)]
    pub var: String,
    pub t: Arc<Expr>,
    pub value: Arc<Expr>,
    pub body: Arc<Expr>,
}

#[pymethods]
impl ELet {
    #[getter]
    fn t(&self) -> Expr {
        (*self.t).clone()
    }

    #[getter]
    fn value(&self) -> Expr {
        (*self.value).clone()
    }

    #[getter]
    fn body(&self) -> Expr {
        (*self.body).clone()
    }
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct ELit {
    pub lit: Literal,
}

#[pymethods]
impl ELit {
    #[getter]
    fn lit(&self) -> Literal {
        self.lit.clone()
    }
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct EMVar {
    #[pyo3(get)]
    pub id: String,
}

/// Expression
///
/// - Sort(ESort)    --- The type of types at universe level `u`.
/// - FVar(EFVar)    --- Free variable with name `name`.
/// - BVar(EBVar)    --- Bound variable with de Bruijn index `idx`.
/// - Const(EConst)  --- Constant with name `name` and universe levels `levels`.
/// - App(Arc<EApp>) --- Application of function `f` to argument `arg`.
/// - Lam(Arc<ELam>) --- Lambda abstraction with variable `var`, type `t`, and body `body`.
/// - Pi(Arc<EPi>)   --- Dependent function type with variable `var`, type `t`, and body `body`.
/// - Let(Arc<ELet>) --- Let binding with variable `var`, type `t`, value `value`, and body `body`.
/// - Lit(ELit)      --- Literal value `lit`.
/// - MVar(EMVar)    --- Metavariable with identifier `id`.
#[derive(Clone, Debug)]
pub enum Expr {
    Sort(ESort),
    FVar(EFVar),
    BVar(EBVar),
    Const(EConst),
    App(Arc<EApp>),
    Lam(Arc<ELam>),
    Pi(Arc<EPi>),
    Let(Arc<ELet>),
    Lit(ELit),
    MVar(EMVar),
}

impl Expr {
    pub fn sort(level: univ_level::UnivLevel) -> Self {
        Self::Sort(ESort { level })
    }

    pub fn fvar(name: impl Into<String>) -> Self {
        Self::FVar(EFVar { name: name.into() })
    }

    pub fn bvar(idx: usize) -> Self {
        Self::BVar(EBVar { idx })
    }

    pub fn const_(name: impl Into<String>, levels: Vec<univ_level::UnivLevel>) -> Self {
        Self::Const(EConst {
            name: name.into(),
            levels,
        })
    }

    pub fn app(f: Arc<Expr>, arg: Arc<Expr>) -> Self {
        Self::App(Arc::new(EApp { f, arg }))
    }

    pub fn lam(var: impl Into<String>, t: Arc<Expr>, body: Arc<Expr>) -> Self {
        Self::Lam(Arc::new(ELam {
            var: var.into(),
            t,
            body,
        }))
    }

    pub fn pi(var: impl Into<String>, t: Arc<Expr>, body: Arc<Expr>) -> Self {
        Self::Pi(Arc::new(EPi {
            var: var.into(),
            t,
            body,
        }))
    }

    pub fn let_(
        var: impl Into<String>,
        t: Arc<Expr>,
        value: Arc<Expr>,
        body: Arc<Expr>,
    ) -> Self {
        Self::Let(Arc::new(ELet {
            var: var.into(),
            t,
            value,
            body,
        }))
    }

    pub fn lit(lit: Literal) -> Self {
        Self::Lit(ELit { lit })
    }

    pub fn mvar(id: impl Into<String>) -> Self {
        Self::MVar(EMVar { id: id.into() })
    }
}

impl Drop for Expr {
    fn drop(&mut self) {
        fn push_children(expr: &mut Expr, stack: &mut Vec<Expr>) {
            match expr {
                Expr::App(app) => {
                    if let Some(inner_app) = Arc::get_mut(app) {
                        if let Some(inner) = Arc::get_mut(&mut inner_app.f) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                        if let Some(inner) = Arc::get_mut(&mut inner_app.arg) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                    }
                }
                Expr::Lam(lam) => {
                    if let Some(inner_lam) = Arc::get_mut(lam) {
                        if let Some(inner) = Arc::get_mut(&mut inner_lam.t) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                        if let Some(inner) = Arc::get_mut(&mut inner_lam.body) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                    }
                }
                Expr::Pi(pi) => {
                    if let Some(inner_pi) = Arc::get_mut(pi) {
                        if let Some(inner) = Arc::get_mut(&mut inner_pi.t) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                        if let Some(inner) = Arc::get_mut(&mut inner_pi.body) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                    }
                }
                Expr::Let(let_expr) => {
                    if let Some(inner_let) = Arc::get_mut(let_expr) {
                        if let Some(inner) = Arc::get_mut(&mut inner_let.t) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                        if let Some(inner) = Arc::get_mut(&mut inner_let.value) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                        if let Some(inner) = Arc::get_mut(&mut inner_let.body) {
                            stack.push(std::mem::replace(inner, Expr::bvar(0)));
                        }
                    }
                }
                Expr::Lit(el) => {
                    if let Literal::Array(items) = &mut el.lit {
                        stack.extend(std::mem::take(items));
                    }
                }
                Expr::Sort(_) | Expr::FVar(_) | Expr::BVar(_) | Expr::Const(_) | Expr::MVar(_) => {}
            }
        }

        let mut stack = Vec::new();
        push_children(self, &mut stack);
        while let Some(mut node) = stack.pop() {
            push_children(&mut node, &mut stack);
        }
    }
}

impl<'py> IntoPyObject<'py> for Expr {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            Expr::Sort(ref s) => s.clone().into_pyobject(py).map(Bound::into_any),
            Expr::FVar(ref v) => v.clone().into_pyobject(py).map(Bound::into_any),
            Expr::BVar(ref b) => b.clone().into_pyobject(py).map(Bound::into_any),
            Expr::Const(ref c) => c.clone().into_pyobject(py).map(Bound::into_any),
            Expr::App(ref a) => (**a).clone().into_pyobject(py).map(Bound::into_any),
            Expr::Lam(ref l) => (**l).clone().into_pyobject(py).map(Bound::into_any),
            Expr::Pi(ref p) => (**p).clone().into_pyobject(py).map(Bound::into_any),
            Expr::Let(ref l) => (**l).clone().into_pyobject(py).map(Bound::into_any),
            Expr::Lit(ref l) => l.clone().into_pyobject(py).map(Bound::into_any),
            Expr::MVar(ref m) => m.clone().into_pyobject(py).map(Bound::into_any),
        }
    }
}

#[derive(FromPyObject)]
enum PyExprRef<'py> {
    Sort(PyRef<'py, ESort>),
    FVar(PyRef<'py, EFVar>),
    BVar(PyRef<'py, EBVar>),
    Const(PyRef<'py, EConst>),
    App(PyRef<'py, EApp>),
    Lam(PyRef<'py, ELam>),
    Pi(PyRef<'py, EPi>),
    Let(PyRef<'py, ELet>),
    Lit(PyRef<'py, ELit>),
    MVar(PyRef<'py, EMVar>),
}

impl<'a, 'py> FromPyObject<'a, 'py> for Expr {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        match ob.extract::<PyExprRef<'py>>()? {
            PyExprRef::Sort(s) => Ok(Expr::Sort(s.clone())),
            PyExprRef::FVar(v) => Ok(Expr::FVar(v.clone())),
            PyExprRef::BVar(b) => Ok(Expr::BVar(b.clone())),
            PyExprRef::Const(c) => Ok(Expr::Const(c.clone())),
            PyExprRef::App(a) => Ok(Expr::App(Arc::new((*a).clone()))),
            PyExprRef::Lam(l) => Ok(Expr::Lam(Arc::new((*l).clone()))),
            PyExprRef::Pi(p) => Ok(Expr::Pi(Arc::new((*p).clone()))),
            PyExprRef::Let(l) => Ok(Expr::Let(Arc::new((*l).clone()))),
            PyExprRef::Lit(l) => Ok(Expr::Lit(l.clone())),
            PyExprRef::MVar(m) => Ok(Expr::MVar(m.clone())),
        }
    }
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ESort>()?;
    m.add_class::<EFVar>()?;
    m.add_class::<EBVar>()?;
    m.add_class::<EConst>()?;
    m.add_class::<EApp>()?;
    m.add_class::<ELam>()?;
    m.add_class::<EPi>()?;
    m.add_class::<ELet>()?;
    m.add_class::<ELit>()?;
    m.add_class::<EMVar>()?;
    Ok(())
}
