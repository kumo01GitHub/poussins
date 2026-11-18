use std::collections::{HashMap, HashSet};
use std::sync::Arc;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyAny;

#[derive(Clone, Debug)]
pub enum UnivLevel {
    Zero,
    Succ(Arc<UnivLevel>),
    Param(String),
    Max(Arc<UnivLevel>, Arc<UnivLevel>),
    IMax(Arc<UnivLevel>, Arc<UnivLevel>),
}

impl Drop for UnivLevel {
    fn drop(&mut self) {
        let mut stack = Vec::new();
        match self {
            UnivLevel::Succ(pred) => {
                if let Some(inner) = Arc::get_mut(pred) {
                    stack.push(std::mem::replace(inner, UnivLevel::Zero));
                }
            }
            UnivLevel::Max(left, right) | UnivLevel::IMax(left, right) => {
                if let Some(inner) = Arc::get_mut(left) {
                    stack.push(std::mem::replace(inner, UnivLevel::Zero));
                }
                if let Some(inner) = Arc::get_mut(right) {
                    stack.push(std::mem::replace(inner, UnivLevel::Zero));
                }
            }
            UnivLevel::Zero | UnivLevel::Param(_) => {}
        }

        while let Some(mut node) = stack.pop() {
            match &mut node {
                UnivLevel::Succ(pred) => {
                    if let Some(inner) = Arc::get_mut(pred) {
                        stack.push(std::mem::replace(inner, UnivLevel::Zero));
                    }
                }
                UnivLevel::Max(left, right) | UnivLevel::IMax(left, right) => {
                    if let Some(inner) = Arc::get_mut(left) {
                        stack.push(std::mem::replace(inner, UnivLevel::Zero));
                    }
                    if let Some(inner) = Arc::get_mut(right) {
                        stack.push(std::mem::replace(inner, UnivLevel::Zero));
                    }
                }
                UnivLevel::Zero | UnivLevel::Param(_) => {}
            }
        }
    }
}

#[pyclass(name = "UnivLevelZero")]
struct PyUnivLevelZero {}

#[pyclass(name = "UnivLevelSucc", get_all)]
struct PyUnivLevelSucc {
    pred: Py<PyAny>,
}

#[pyclass(name = "UnivLevelParam", get_all)]
struct PyUnivLevelParam {
    name: String,
}

#[pyclass(name = "UnivLevelMax", get_all)]
struct PyUnivLevelMax {
    left: Py<PyAny>,
    right: Py<PyAny>,
}

#[pyclass(name = "UnivLevelIMax", get_all)]
struct PyUnivLevelIMax {
    left: Py<PyAny>,
    right: Py<PyAny>,
}

impl<'py> IntoPyObject<'py> for UnivLevel {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        enum Task {
            Visit(Arc<UnivLevel>),
            BuildSucc,
            BuildMax,
            BuildIMax,
        }

        let mut tasks = vec![Task::Visit(Arc::new(self))];
        let mut results: Vec<Bound<'py, PyAny>> = Vec::new();

        while let Some(task) = tasks.pop() {
            match task {
                Task::Visit(lvl) => match &*lvl {
                    UnivLevel::Zero => {
                        results.push(Bound::new(py, PyUnivLevelZero {})?.into_any());
                    }
                    UnivLevel::Param(name) => {
                        results.push(
                            Bound::new(py, PyUnivLevelParam { name: name.clone() })?.into_any(),
                        );
                    }
                    UnivLevel::Succ(pred) => {
                        tasks.push(Task::BuildSucc);
                        tasks.push(Task::Visit(Arc::clone(pred)));
                    }
                    UnivLevel::Max(left, right) => {
                        tasks.push(Task::BuildMax);
                        tasks.push(Task::Visit(Arc::clone(right)));
                        tasks.push(Task::Visit(Arc::clone(left)));
                    }
                    UnivLevel::IMax(left, right) => {
                        tasks.push(Task::BuildIMax);
                        tasks.push(Task::Visit(Arc::clone(right)));
                        tasks.push(Task::Visit(Arc::clone(left)));
                    }
                },
                Task::BuildSucc => {
                    let pred = results.pop().unwrap().unbind();
                    results.push(Bound::new(py, PyUnivLevelSucc { pred })?.into_any());
                }
                Task::BuildMax => {
                    let right = results.pop().unwrap().unbind();
                    let left = results.pop().unwrap().unbind();
                    results.push(Bound::new(py, PyUnivLevelMax { left, right })?.into_any());
                }
                Task::BuildIMax => {
                    let right = results.pop().unwrap().unbind();
                    let left = results.pop().unwrap().unbind();
                    results.push(Bound::new(py, PyUnivLevelIMax { left, right })?.into_any());
                }
            }
        }

        Ok(results.pop().unwrap())
    }
}

#[derive(FromPyObject)]
#[allow(dead_code)]
enum PyUnivLevel<'py> {
    Zero(PyRef<'py, PyUnivLevelZero>),
    Succ(PyRef<'py, PyUnivLevelSucc>),
    Param(PyRef<'py, PyUnivLevelParam>),
    Max(PyRef<'py, PyUnivLevelMax>),
    IMax(PyRef<'py, PyUnivLevelIMax>),
}

impl<'a, 'py> FromPyObject<'a, 'py> for UnivLevel {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        enum Task<'py> {
            Enter(Bound<'py, PyAny>),
            ExitSucc(usize),
            ExitMax(usize),
            ExitIMax(usize),
        }

        let mut tasks = vec![Task::Enter(ob.to_owned())];
        let mut results: Vec<Arc<UnivLevel>> = Vec::new();
        let mut visiting: HashSet<usize> = HashSet::new();
        let mut memo: HashMap<usize, Arc<UnivLevel>> = HashMap::new();

        while let Some(task) = tasks.pop() {
            match task {
                Task::Enter(node) => {
                    let ptr = node.as_ptr() as usize;
                    if let Some(cached) = memo.get(&ptr) {
                        results.push(Arc::clone(cached));
                        continue;
                    }
                    if !visiting.insert(ptr) {
                        return Err(PyValueError::new_err(
                            "Cyclic UnivLevel structure detected.",
                        ));
                    }

                    match node.extract::<PyUnivLevel<'py>>()? {
                        PyUnivLevel::Zero(_) => {
                            visiting.remove(&ptr);
                            let res = Arc::new(UnivLevel::Zero);
                            memo.insert(ptr, Arc::clone(&res));
                            results.push(res);
                        }
                        PyUnivLevel::Param(p) => {
                            let name = p.name.clone();
                            drop(p);
                            visiting.remove(&ptr);
                            let res = Arc::new(UnivLevel::Param(name));
                            memo.insert(ptr, Arc::clone(&res));
                            results.push(res);
                        }
                        PyUnivLevel::Succ(s) => {
                            let pred = s.pred.bind(node.py()).clone();
                            drop(s);
                            tasks.push(Task::ExitSucc(ptr));
                            tasks.push(Task::Enter(pred));
                        }
                        PyUnivLevel::Max(m) => {
                            let left = m.left.bind(node.py()).clone();
                            let right = m.right.bind(node.py()).clone();
                            drop(m);
                            tasks.push(Task::ExitMax(ptr));
                            tasks.push(Task::Enter(right));
                            tasks.push(Task::Enter(left));
                        }
                        PyUnivLevel::IMax(im) => {
                            let left = im.left.bind(node.py()).clone();
                            let right = im.right.bind(node.py()).clone();
                            drop(im);
                            tasks.push(Task::ExitIMax(ptr));
                            tasks.push(Task::Enter(right));
                            tasks.push(Task::Enter(left));
                        }
                    }
                }
                Task::ExitSucc(ptr) => {
                    visiting.remove(&ptr);
                    let pred = results.pop().unwrap();
                    let res = Arc::new(UnivLevel::Succ(pred));
                    memo.insert(ptr, Arc::clone(&res));
                    results.push(res);
                }
                Task::ExitMax(ptr) => {
                    visiting.remove(&ptr);
                    let right = results.pop().unwrap();
                    let left = results.pop().unwrap();
                    let res = Arc::new(UnivLevel::Max(left, right));
                    memo.insert(ptr, Arc::clone(&res));
                    results.push(res);
                }
                Task::ExitIMax(ptr) => {
                    visiting.remove(&ptr);
                    let right = results.pop().unwrap();
                    let left = results.pop().unwrap();
                    let res = Arc::new(UnivLevel::IMax(left, right));
                    memo.insert(ptr, Arc::clone(&res));
                    results.push(res);
                }
            }
        }

        let root = results.pop().unwrap();
        Ok(Arc::try_unwrap(root).unwrap_or_else(|arc| (*arc).clone()))
    }
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyUnivLevelZero>()?;
    m.add_class::<PyUnivLevelSucc>()?;
    m.add_class::<PyUnivLevelParam>()?;
    m.add_class::<PyUnivLevelMax>()?;
    m.add_class::<PyUnivLevelIMax>()?;
    Ok(())
}
