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

#[pyclass(name = "UnivLevelSucc", get_all)]
struct PyUnivLevelSucc {
    pred: UnivLevel,
}

#[pyclass(name = "UnivLevelParam", get_all)]
struct PyUnivLevelParam {
    name: String,
}

#[pyclass(name = "UnivLevelMax", get_all)]
struct PyUnivLevelMax {
    left: UnivLevel,
    right: UnivLevel,
}

#[pyclass(name = "UnivLevelIMax", get_all)]
struct PyUnivLevelIMax {
    left: UnivLevel,
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
        match ob.extract::<PyUnivLevel<'py>>()? {
            PyUnivLevel::Zero(_) => Ok(UnivLevel::Zero),
            PyUnivLevel::Succ(s) => Ok(UnivLevel::Succ(Box::new(s.pred.clone()))),
            PyUnivLevel::Param(p) => Ok(UnivLevel::Param(p.name.clone())),
            PyUnivLevel::Max(m) => Ok(UnivLevel::Max(
                Box::new(m.left.clone()),
                Box::new(m.right.clone()),
            )),
            PyUnivLevel::IMax(im) => Ok(UnivLevel::IMax(
                Box::new(im.left.clone()),
                Box::new(im.right.clone()),
            )),
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
