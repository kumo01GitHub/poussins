use std::collections::{HashMap, HashSet};
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
    App(Arc<Expr>, Arc<Expr>),
    Lam(String, Arc<Expr>, Arc<Expr>),
    Pi(String, Arc<Expr>, Arc<Expr>),
    Let(String, Arc<Expr>, Arc<Expr>, Arc<Expr>),
    Lit(Literal),
    MVar(String),
}

impl Drop for Expr {
    fn drop(&mut self) {
        fn push_children(expr: &mut Expr, stack: &mut Vec<Expr>) {
            match expr {
                Expr::App(f, arg) => {
                    if let Some(inner) = Arc::get_mut(f) {
                        stack.push(std::mem::replace(inner, Expr::BVar(0)));
                    }
                    if let Some(inner) = Arc::get_mut(arg) {
                        stack.push(std::mem::replace(inner, Expr::BVar(0)));
                    }
                }
                Expr::Lam(_, t, body) | Expr::Pi(_, t, body) => {
                    if let Some(inner) = Arc::get_mut(t) {
                        stack.push(std::mem::replace(inner, Expr::BVar(0)));
                    }
                    if let Some(inner) = Arc::get_mut(body) {
                        stack.push(std::mem::replace(inner, Expr::BVar(0)));
                    }
                }
                Expr::Let(_, t, val, body) => {
                    if let Some(inner) = Arc::get_mut(t) {
                        stack.push(std::mem::replace(inner, Expr::BVar(0)));
                    }
                    if let Some(inner) = Arc::get_mut(val) {
                        stack.push(std::mem::replace(inner, Expr::BVar(0)));
                    }
                    if let Some(inner) = Arc::get_mut(body) {
                        stack.push(std::mem::replace(inner, Expr::BVar(0)));
                    }
                }
                Expr::Lit(Literal::Array(items)) => {
                    stack.extend(std::mem::take(items));
                }
                Expr::Sort(_)
                | Expr::FVar(_)
                | Expr::BVar(_)
                | Expr::Const(_, _)
                | Expr::Lit(_)
                | Expr::MVar(_) => {}
            }
        }

        let mut stack = Vec::new();
        push_children(self, &mut stack);
        while let Some(mut node) = stack.pop() {
            push_children(&mut node, &mut stack);
        }
    }
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
    f: Py<PyAny>,
    arg: Py<PyAny>,
}

#[pyclass(name = "ELam", get_all)]
struct PyLam {
    var: String,
    t: Py<PyAny>,
    body: Py<PyAny>,
}

#[pyclass(name = "EPi", get_all)]
struct PyPi {
    var: String,
    t: Py<PyAny>,
    body: Py<PyAny>,
}

#[pyclass(name = "ELet", get_all)]
struct PyLet {
    var: String,
    t: Py<PyAny>,
    value: Py<PyAny>,
    body: Py<PyAny>,
}

#[pyclass(name = "ELit", get_all)]
struct PyLit {
    lit: Py<PyAny>,
}

#[pyclass(name = "EMVar", get_all)]
struct PyMVar {
    id: String,
}

fn expr_to_py_iterative<'py>(py: Python<'py>, root: Expr) -> PyResult<Bound<'py, PyAny>> {
    enum Task {
        Visit(Arc<Expr>),
        BuildApp,
        BuildLam(String),
        BuildPi(String),
        BuildLet(String),
        BuildLitArray(usize),
    }

    let mut tasks = vec![Task::Visit(Arc::new(root))];
    let mut results: Vec<Bound<'py, PyAny>> = Vec::new();

    while let Some(task) = tasks.pop() {
        match task {
            Task::Visit(expr) => match &*expr {
                Expr::Sort(level) => {
                    results.push(
                        Bound::new(
                            py,
                            PySort {
                                level: level.clone(),
                            },
                        )?
                        .into_any(),
                    );
                }
                Expr::FVar(name) => {
                    results.push(Bound::new(py, PyFVar { name: name.clone() })?.into_any());
                }
                Expr::BVar(idx) => {
                    results.push(Bound::new(py, PyBVar { idx: *idx })?.into_any());
                }
                Expr::Const(name, levels) => {
                    results.push(
                        Bound::new(
                            py,
                            PyConst {
                                name: name.clone(),
                                levels: levels.clone(),
                            },
                        )?
                        .into_any(),
                    );
                }
                Expr::MVar(id) => {
                    results.push(Bound::new(py, PyMVar { id: id.clone() })?.into_any());
                }
                Expr::App(f, arg) => {
                    tasks.push(Task::BuildApp);
                    tasks.push(Task::Visit(Arc::clone(arg)));
                    tasks.push(Task::Visit(Arc::clone(f)));
                }
                Expr::Lam(var, t, body) => {
                    tasks.push(Task::BuildLam(var.clone()));
                    tasks.push(Task::Visit(Arc::clone(body)));
                    tasks.push(Task::Visit(Arc::clone(t)));
                }
                Expr::Pi(var, t, body) => {
                    tasks.push(Task::BuildPi(var.clone()));
                    tasks.push(Task::Visit(Arc::clone(body)));
                    tasks.push(Task::Visit(Arc::clone(t)));
                }
                Expr::Let(var, t, value, body) => {
                    tasks.push(Task::BuildLet(var.clone()));
                    tasks.push(Task::Visit(Arc::clone(body)));
                    tasks.push(Task::Visit(Arc::clone(value)));
                    tasks.push(Task::Visit(Arc::clone(t)));
                }
                Expr::Lit(lit) => match lit {
                    Literal::Nat(val) => {
                        let py_lit = val.into_pyobject(py)?.into_any().unbind();
                        results.push(Bound::new(py, PyLit { lit: py_lit })?.into_any());
                    }
                    Literal::Float(val) => {
                        let py_lit = val.into_pyobject(py)?.into_any().unbind();
                        results.push(Bound::new(py, PyLit { lit: py_lit })?.into_any());
                    }
                    Literal::String(val) => {
                        let py_lit = val.into_pyobject(py)?.into_any().unbind();
                        results.push(Bound::new(py, PyLit { lit: py_lit })?.into_any());
                    }
                    Literal::Array(items) => {
                        let len = items.len();
                        tasks.push(Task::BuildLitArray(len));
                        for item in items.iter().rev() {
                            tasks.push(Task::Visit(Arc::new(item.clone())));
                        }
                    }
                },
            },
            Task::BuildApp => {
                let arg = results.pop().unwrap().unbind();
                let f = results.pop().unwrap().unbind();
                results.push(Bound::new(py, PyApp { f, arg })?.into_any());
            }
            Task::BuildLam(var) => {
                let body = results.pop().unwrap().unbind();
                let t = results.pop().unwrap().unbind();
                results.push(Bound::new(py, PyLam { var, t, body })?.into_any());
            }
            Task::BuildPi(var) => {
                let body = results.pop().unwrap().unbind();
                let t = results.pop().unwrap().unbind();
                results.push(Bound::new(py, PyPi { var, t, body })?.into_any());
            }
            Task::BuildLet(var) => {
                let body = results.pop().unwrap().unbind();
                let value = results.pop().unwrap().unbind();
                let t = results.pop().unwrap().unbind();
                results.push(
                    Bound::new(
                        py,
                        PyLet {
                            var,
                            t,
                            value,
                            body,
                        },
                    )?
                    .into_any(),
                );
            }
            Task::BuildLitArray(len) => {
                let start = results.len() - len;
                let items: Vec<Bound<'py, PyAny>> = results.drain(start..).collect();
                let py_list = PyList::new(py, items)?.into_any().unbind();
                results.push(Bound::new(py, PyLit { lit: py_list })?.into_any());
            }
        }
    }

    Ok(results.pop().unwrap())
}

impl<'py> IntoPyObject<'py> for Expr {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        expr_to_py_iterative(py, self)
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
            Literal::Array(vals) => {
                let mut py_vals = Vec::with_capacity(vals.len());
                for v in vals {
                    py_vals.push(expr_to_py_iterative(py, v)?);
                }
                Ok(PyList::new(py, py_vals)?.into_any())
            }
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

fn extract_expr_iterative<'py>(root: Bound<'py, PyAny>) -> PyResult<Expr> {
    enum Task<'py> {
        Enter(Bound<'py, PyAny>),
        ExitApp(usize),
        ExitLam(usize, String),
        ExitPi(usize, String),
        ExitLet(usize, String),
        ExitLitArray(usize, usize),
    }

    let mut tasks = vec![Task::Enter(root)];
    let mut results: Vec<Arc<Expr>> = Vec::new();
    let mut visiting: HashSet<usize> = HashSet::new();
    let mut memo: HashMap<usize, Arc<Expr>> = HashMap::new();

    while let Some(task) = tasks.pop() {
        match task {
            Task::Enter(node) => {
                let ptr = node.as_ptr() as usize;
                if let Some(cached) = memo.get(&ptr) {
                    results.push(Arc::clone(cached));
                    continue;
                }
                if !visiting.insert(ptr) {
                    return Err(PyValueError::new_err("Cyclic Expr structure detected."));
                }

                match node.extract::<PyExpr<'py>>()? {
                    PyExpr::Sort(s) => {
                        let level = s.level.clone();
                        drop(s);
                        visiting.remove(&ptr);
                        let res = Arc::new(Expr::Sort(level));
                        memo.insert(ptr, Arc::clone(&res));
                        results.push(res);
                    }
                    PyExpr::FVar(v) => {
                        let name = v.name.clone();
                        drop(v);
                        visiting.remove(&ptr);
                        let res = Arc::new(Expr::FVar(name));
                        memo.insert(ptr, Arc::clone(&res));
                        results.push(res);
                    }
                    PyExpr::BVar(b) => {
                        let idx = b.idx;
                        drop(b);
                        visiting.remove(&ptr);
                        let res = Arc::new(Expr::BVar(idx));
                        memo.insert(ptr, Arc::clone(&res));
                        results.push(res);
                    }
                    PyExpr::Const(c) => {
                        let name = c.name.clone();
                        let levels = c.levels.clone();
                        drop(c);
                        visiting.remove(&ptr);
                        let res = Arc::new(Expr::Const(name, levels));
                        memo.insert(ptr, Arc::clone(&res));
                        results.push(res);
                    }
                    PyExpr::MVar(m) => {
                        let id = m.id.clone();
                        drop(m);
                        visiting.remove(&ptr);
                        let res = Arc::new(Expr::MVar(id));
                        memo.insert(ptr, Arc::clone(&res));
                        results.push(res);
                    }
                    PyExpr::App(a) => {
                        let py = node.py();
                        let f = a.f.bind(py).clone();
                        let arg = a.arg.bind(py).clone();
                        drop(a);
                        tasks.push(Task::ExitApp(ptr));
                        tasks.push(Task::Enter(arg));
                        tasks.push(Task::Enter(f));
                    }
                    PyExpr::Lam(l) => {
                        let py = node.py();
                        let var = l.var.clone();
                        let t = l.t.bind(py).clone();
                        let body = l.body.bind(py).clone();
                        drop(l);
                        tasks.push(Task::ExitLam(ptr, var));
                        tasks.push(Task::Enter(body));
                        tasks.push(Task::Enter(t));
                    }
                    PyExpr::Pi(p) => {
                        let py = node.py();
                        let var = p.var.clone();
                        let t = p.t.bind(py).clone();
                        let body = p.body.bind(py).clone();
                        drop(p);
                        tasks.push(Task::ExitPi(ptr, var));
                        tasks.push(Task::Enter(body));
                        tasks.push(Task::Enter(t));
                    }
                    PyExpr::Let(l) => {
                        let py = node.py();
                        let var = l.var.clone();
                        let t = l.t.bind(py).clone();
                        let value = l.value.bind(py).clone();
                        let body = l.body.bind(py).clone();
                        drop(l);
                        tasks.push(Task::ExitLet(ptr, var));
                        tasks.push(Task::Enter(body));
                        tasks.push(Task::Enter(value));
                        tasks.push(Task::Enter(t));
                    }
                    PyExpr::Lit(l) => {
                        let py = node.py();
                        let lit_ob = l.lit.bind(py).clone();
                        drop(l);

                        if lit_ob.is_instance_of::<PyBool>() {
                            visiting.remove(&ptr);
                            return Err(PyTypeError::new_err(
                                "Expected int (non-negative), float, str, or list for Literal, got bool",
                            ));
                        } else if lit_ob.is_instance_of::<PyInt>() {
                            let val = lit_ob.extract::<u64>().map_err(|_| {
                                PyValueError::new_err(
                                    "Natural number literal must be a non-negative integer within u64 range.",
                                )
                            })?;
                            visiting.remove(&ptr);
                            let res = Arc::new(Expr::Lit(Literal::Nat(val)));
                            memo.insert(ptr, Arc::clone(&res));
                            results.push(res);
                        } else if lit_ob.is_instance_of::<PyFloat>() {
                            let val = lit_ob.extract::<f64>()?;
                            visiting.remove(&ptr);
                            let res = Arc::new(Expr::Lit(Literal::Float(val)));
                            memo.insert(ptr, Arc::clone(&res));
                            results.push(res);
                        } else if lit_ob.is_instance_of::<PyString>() {
                            let val = lit_ob.extract::<String>()?;
                            visiting.remove(&ptr);
                            let res = Arc::new(Expr::Lit(Literal::String(val)));
                            memo.insert(ptr, Arc::clone(&res));
                            results.push(res);
                        } else if let Ok(list) = lit_ob.cast::<PyList>() {
                            let len = list.len();
                            tasks.push(Task::ExitLitArray(ptr, len));
                            for item in list.iter().rev() {
                                tasks.push(Task::Enter(item));
                            }
                        } else {
                            visiting.remove(&ptr);
                            let type_name = lit_ob.get_type().name()?;
                            return Err(PyTypeError::new_err(format!(
                                "Expected int (non-negative), float, str, or list for Literal, got {type_name}"
                            )));
                        }
                    }
                }
            }
            Task::ExitApp(ptr) => {
                visiting.remove(&ptr);
                let arg = results.pop().unwrap();
                let f = results.pop().unwrap();
                let res = Arc::new(Expr::App(f, arg));
                memo.insert(ptr, Arc::clone(&res));
                results.push(res);
            }
            Task::ExitLam(ptr, var) => {
                visiting.remove(&ptr);
                let body = results.pop().unwrap();
                let t = results.pop().unwrap();
                let res = Arc::new(Expr::Lam(var, t, body));
                memo.insert(ptr, Arc::clone(&res));
                results.push(res);
            }
            Task::ExitPi(ptr, var) => {
                visiting.remove(&ptr);
                let body = results.pop().unwrap();
                let t = results.pop().unwrap();
                let res = Arc::new(Expr::Pi(var, t, body));
                memo.insert(ptr, Arc::clone(&res));
                results.push(res);
            }
            Task::ExitLet(ptr, var) => {
                visiting.remove(&ptr);
                let body = results.pop().unwrap();
                let value = results.pop().unwrap();
                let t = results.pop().unwrap();
                let res = Arc::new(Expr::Let(var, t, value, body));
                memo.insert(ptr, Arc::clone(&res));
                results.push(res);
            }
            Task::ExitLitArray(ptr, len) => {
                visiting.remove(&ptr);
                let start = results.len() - len;
                let items: Vec<Expr> = results
                    .drain(start..)
                    .map(|arc| Arc::try_unwrap(arc).unwrap_or_else(|a| (*a).clone()))
                    .collect();
                let res = Arc::new(Expr::Lit(Literal::Array(items)));
                memo.insert(ptr, Arc::clone(&res));
                results.push(res);
            }
        }
    }

    let root_arc = results.pop().unwrap();
    Ok(Arc::try_unwrap(root_arc).unwrap_or_else(|arc| (*arc).clone()))
}

impl<'a, 'py> FromPyObject<'a, 'py> for Expr {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        extract_expr_iterative(ob.to_owned())
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
                items.push(extract_expr_iterative(item)?);
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
