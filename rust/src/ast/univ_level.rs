use pyo3::prelude::*;
use pyo3::types::PyAny;

#[derive(Clone)]
pub enum UnivLevel {
    Zero,
    Succ(Box<UnivLevel>),
    Param(String),
    Max(Box<UnivLevel>, Box<UnivLevel>),
    IMax(Box<UnivLevel>, Box<UnivLevel>),
}

#[pyclass(name = "UnivLevelZero")]
struct PyUnivLevelZero {}

#[pyclass(name = "UnivLevelSucc")]
struct PyUnivLevelSucc {
    pred: Box<UnivLevel>,
}

#[pymethods]
impl PyUnivLevelSucc {
    #[getter]
    fn pred(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.pred.clone())
    }
}

#[pyclass(name = "UnivLevelParam")]
struct PyUnivLevelParam {
    #[pyo3(get)]
    name: String,
}

#[pyclass(name = "UnivLevelMax")]
struct PyUnivLevelMax {
    left: Box<UnivLevel>,
    right: Box<UnivLevel>,
}

#[pymethods]
impl PyUnivLevelMax {
    #[getter]
    fn left(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.left.clone())
    }

    #[getter]
    fn right(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.right.clone())
    }
}

#[pyclass(name = "UnivLevelIMax")]
struct PyUnivLevelIMax {
    left: Box<UnivLevel>,
    right: Box<UnivLevel>,
}

#[pymethods]
impl PyUnivLevelIMax {
    #[getter]
    fn left(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.left.clone())
    }

    #[getter]
    fn right(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        to_pyresult(py, *self.right.clone())
    }
}

pub fn to_pyresult(py: Python<'_>, level: UnivLevel) -> PyResult<Py<PyAny>> {
    match level {
        UnivLevel::Zero => Ok(Bound::new(py, PyUnivLevelZero {})?.into_any().unbind()),
        UnivLevel::Succ(pred) => Ok(Bound::new(py, PyUnivLevelSucc { pred })?
            .into_any()
            .unbind()),
        UnivLevel::Param(name) => Ok(Bound::new(py, PyUnivLevelParam { name })?
            .into_any()
            .unbind()),
        UnivLevel::Max(left, right) => Ok(Bound::new(py, PyUnivLevelMax { left, right })?
            .into_any()
            .unbind()),
        UnivLevel::IMax(left, right) => Ok(Bound::new(py, PyUnivLevelIMax { left, right })?
            .into_any()
            .unbind()),
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
