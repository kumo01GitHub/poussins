use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::PyAny;

#[derive(Clone, Debug)]
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
    #[pyo3(get)]
    pred: UnivLevel,
}

#[pyclass(name = "UnivLevelParam")]
struct PyUnivLevelParam {
    #[pyo3(get)]
    name: String,
}

#[pyclass(name = "UnivLevelMax")]
struct PyUnivLevelMax {
    #[pyo3(get)]
    left: UnivLevel,
    #[pyo3(get)]
    right: UnivLevel,
}

#[pyclass(name = "UnivLevelIMax")]
struct PyUnivLevelIMax {
    #[pyo3(get)]
    left: UnivLevel,
    #[pyo3(get)]
    right: UnivLevel,
}

impl<'py> IntoPyObject<'py> for UnivLevel {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            UnivLevel::Zero => Ok(Bound::new(py, PyUnivLevelZero {})?.into_any()),
            UnivLevel::Succ(pred) => Ok(Bound::new(py, PyUnivLevelSucc { pred: *pred })?.into_any()),
            UnivLevel::Param(name) => Ok(Bound::new(py, PyUnivLevelParam { name })?.into_any()),
            UnivLevel::Max(left, right) => Ok(Bound::new(
                py,
                PyUnivLevelMax {
                    left: *left,
                    right: *right,
                },
            )?
            .into_any()),
            UnivLevel::IMax(left, right) => Ok(Bound::new(
                py,
                PyUnivLevelIMax {
                    left: *left,
                    right: *right,
                },
            )?
            .into_any()),
        }
    }
}

impl<'a, 'py> FromPyObject<'a, 'py> for UnivLevel {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        if ob.is_instance_of::<PyUnivLevelZero>() {
            Ok(UnivLevel::Zero)
        } else if let Ok(s) = ob.extract::<PyRef<'_, PyUnivLevelSucc>>() {
            Ok(UnivLevel::Succ(Box::new(s.pred.clone())))
        } else if let Ok(p) = ob.extract::<PyRef<'_, PyUnivLevelParam>>() {
            Ok(UnivLevel::Param(p.name.clone()))
        } else if let Ok(m) = ob.extract::<PyRef<'_, PyUnivLevelMax>>() {
            Ok(UnivLevel::Max(
                Box::new(m.left.clone()),
                Box::new(m.right.clone()),
            ))
        } else if let Ok(im) = ob.extract::<PyRef<'_, PyUnivLevelIMax>>() {
            Ok(UnivLevel::IMax(
                Box::new(im.left.clone()),
                Box::new(im.right.clone()),
            ))
        } else {
            Err(PyTypeError::new_err("Expected a UnivLevel instance"))
        }
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