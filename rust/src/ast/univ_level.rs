use std::sync::Arc;

use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::PyAny;

// ---------------------------------------------------------------------------
// Struct variants (each is a #[pyclass] exposed to Python)
// ---------------------------------------------------------------------------

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct UnivLevelZero;

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct UnivLevelSucc {
    pub pred: Arc<UnivLevel>,
}

impl PartialEq for UnivLevelSucc {
    fn eq(&self, other: &Self) -> bool {
        Arc::ptr_eq(&self.pred, &other.pred) || self.pred == other.pred
    }
}
impl Eq for UnivLevelSucc {}

impl std::hash::Hash for UnivLevelSucc {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.pred.hash(state);
    }
}

#[pymethods]
impl UnivLevelSucc {
    #[getter]
    fn pred(&self) -> UnivLevel {
        (*self.pred).clone()
    }
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct UnivLevelParam {
    #[pyo3(get)]
    pub name: String,
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct UnivLevelMax {
    pub left: Arc<UnivLevel>,
    pub right: Arc<UnivLevel>,
}

impl PartialEq for UnivLevelMax {
    fn eq(&self, other: &Self) -> bool {
        (Arc::ptr_eq(&self.left, &other.left) || self.left == other.left)
            && (Arc::ptr_eq(&self.right, &other.right) || self.right == other.right)
    }
}
impl Eq for UnivLevelMax {}

impl std::hash::Hash for UnivLevelMax {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.left.hash(state);
        self.right.hash(state);
    }
}

#[pymethods]
impl UnivLevelMax {
    #[getter]
    fn left(&self) -> UnivLevel {
        (*self.left).clone()
    }

    #[getter]
    fn right(&self) -> UnivLevel {
        (*self.right).clone()
    }
}

#[pyclass(module = "poussins._core", frozen)]
#[derive(Clone, Debug)]
pub struct UnivLevelIMax {
    pub left: Arc<UnivLevel>,
    pub right: Arc<UnivLevel>,
}

impl PartialEq for UnivLevelIMax {
    fn eq(&self, other: &Self) -> bool {
        (Arc::ptr_eq(&self.left, &other.left) || self.left == other.left)
            && (Arc::ptr_eq(&self.right, &other.right) || self.right == other.right)
    }
}
impl Eq for UnivLevelIMax {}

impl std::hash::Hash for UnivLevelIMax {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.left.hash(state);
        self.right.hash(state);
    }
}

#[pymethods]
impl UnivLevelIMax {
    #[getter]
    fn left(&self) -> UnivLevel {
        (*self.left).clone()
    }

    #[getter]
    fn right(&self) -> UnivLevel {
        (*self.right).clone()
    }
}

// ---------------------------------------------------------------------------
// UnivLevel enum — mirrors the Expr pattern
// ---------------------------------------------------------------------------

/// Universe level.
///
/// - `Zero`               — Level 0.
/// - `Succ(Arc<…>)`       — Successor of a level.
/// - `Param(…)`           — Named universe parameter.
/// - `Max(Arc<…>)`        — Maximum of two levels.
/// - `IMax(Arc<…>)`       — Impredicative maximum of two levels.
#[derive(Clone, Debug)]
pub enum UnivLevel {
    Zero(UnivLevelZero),
    Succ(Arc<UnivLevelSucc>),
    Param(UnivLevelParam),
    Max(Arc<UnivLevelMax>),
    IMax(Arc<UnivLevelIMax>),
}

impl UnivLevel {
    /// Create the zero universe level.
    pub fn zero() -> Self {
        Self::Zero(UnivLevelZero)
    }

    /// Create a successor universe level.
    pub fn succ(pred: Arc<UnivLevel>) -> Self {
        Self::Succ(Arc::new(UnivLevelSucc { pred }))
    }

    /// Create a named universe parameter.
    pub fn param(name: impl Into<String>) -> Self {
        Self::Param(UnivLevelParam { name: name.into() })
    }

    /// Create a max universe level.
    pub fn max(left: Arc<UnivLevel>, right: Arc<UnivLevel>) -> Self {
        Self::Max(Arc::new(UnivLevelMax { left, right }))
    }

    /// Create an imax universe level.
    pub fn imax(left: Arc<UnivLevel>, right: Arc<UnivLevel>) -> Self {
        Self::IMax(Arc::new(UnivLevelIMax { left, right }))
    }
}

impl PartialEq for UnivLevel {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Self::Zero(a), Self::Zero(b)) => a == b,
            (Self::Succ(a), Self::Succ(b)) => Arc::ptr_eq(a, b) || a == b,
            (Self::Param(a), Self::Param(b)) => a == b,
            (Self::Max(a), Self::Max(b)) => Arc::ptr_eq(a, b) || a == b,
            (Self::IMax(a), Self::IMax(b)) => Arc::ptr_eq(a, b) || a == b,
            _ => false,
        }
    }
}

impl Eq for UnivLevel {}

impl std::hash::Hash for UnivLevel {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        std::mem::discriminant(self).hash(state);
        match self {
            Self::Zero(z) => z.hash(state),
            Self::Succ(s) => s.hash(state),
            Self::Param(p) => p.hash(state),
            Self::Max(m) => m.hash(state),
            Self::IMax(im) => im.hash(state),
        }
    }
}

// ---------------------------------------------------------------------------
// Iterative Drop — prevents stack overflow on deeply nested levels
// ---------------------------------------------------------------------------

impl Drop for UnivLevel {
    fn drop(&mut self) {
        fn push_children(lvl: &mut UnivLevel, stack: &mut Vec<UnivLevel>) {
            match lvl {
                UnivLevel::Succ(s) => {
                    if let Some(inner_s) = Arc::get_mut(s) {
                        if let Some(inner) = Arc::get_mut(&mut inner_s.pred) {
                            // Replace the child with a trivial sentinel before pushing
                            // so the original Arc drops without recursion.
                            stack.push(std::mem::replace(inner, UnivLevel::zero()));
                        }
                    }
                }
                UnivLevel::Max(m) => {
                    if let Some(inner_m) = Arc::get_mut(m) {
                        if let Some(inner) = Arc::get_mut(&mut inner_m.left) {
                            stack.push(std::mem::replace(inner, UnivLevel::zero()));
                        }
                        if let Some(inner) = Arc::get_mut(&mut inner_m.right) {
                            stack.push(std::mem::replace(inner, UnivLevel::zero()));
                        }
                    }
                }
                UnivLevel::IMax(im) => {
                    if let Some(inner_im) = Arc::get_mut(im) {
                        if let Some(inner) = Arc::get_mut(&mut inner_im.left) {
                            stack.push(std::mem::replace(inner, UnivLevel::zero()));
                        }
                        if let Some(inner) = Arc::get_mut(&mut inner_im.right) {
                            stack.push(std::mem::replace(inner, UnivLevel::zero()));
                        }
                    }
                }
                UnivLevel::Zero(_) | UnivLevel::Param(_) => {}
            }
        }

        let mut stack = Vec::new();
        push_children(self, &mut stack);
        while let Some(mut node) = stack.pop() {
            push_children(&mut node, &mut stack);
        }
    }
}

// ---------------------------------------------------------------------------
// IntoPyObject — converts UnivLevel → Python object (the struct IS the pyclass)
// ---------------------------------------------------------------------------

impl<'py> IntoPyObject<'py> for UnivLevel {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            UnivLevel::Zero(ref z) => z.clone().into_pyobject(py).map(Bound::into_any),
            UnivLevel::Succ(ref s) => (**s).clone().into_pyobject(py).map(Bound::into_any),
            UnivLevel::Param(ref p) => p.clone().into_pyobject(py).map(Bound::into_any),
            UnivLevel::Max(ref m) => (**m).clone().into_pyobject(py).map(Bound::into_any),
            UnivLevel::IMax(ref im) => (**im).clone().into_pyobject(py).map(Bound::into_any),
        }
    }
}

// ---------------------------------------------------------------------------
// FromPyObject — converts Python object → UnivLevel via PyRef extraction
// ---------------------------------------------------------------------------

#[derive(FromPyObject)]
#[allow(dead_code)]
enum PyUnivLevelRef<'py> {
    Zero(PyRef<'py, UnivLevelZero>),
    Succ(PyRef<'py, UnivLevelSucc>),
    Param(PyRef<'py, UnivLevelParam>),
    Max(PyRef<'py, UnivLevelMax>),
    IMax(PyRef<'py, UnivLevelIMax>),
}

impl<'a, 'py> FromPyObject<'a, 'py> for UnivLevel {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        match ob.extract::<PyUnivLevelRef<'py>>() {
            Ok(r) => match r {
                PyUnivLevelRef::Zero(_) => Ok(UnivLevel::Zero(UnivLevelZero)),
                PyUnivLevelRef::Succ(s) => Ok(UnivLevel::Succ(Arc::new((*s).clone()))),
                PyUnivLevelRef::Param(p) => Ok(UnivLevel::Param((*p).clone())),
                PyUnivLevelRef::Max(m) => Ok(UnivLevel::Max(Arc::new((*m).clone()))),
                PyUnivLevelRef::IMax(im) => Ok(UnivLevel::IMax(Arc::new((*im).clone()))),
            },
            Err(_) => {
                let type_name = ob.get_type().name()?;
                Err(PyTypeError::new_err(format!(
                    "Expected a UnivLevel variant (UnivLevelZero, UnivLevelSucc, \
                     UnivLevelParam, UnivLevelMax, UnivLevelIMax), got {type_name}"
                )))
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Module registration
// ---------------------------------------------------------------------------

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<UnivLevelZero>()?;
    m.add_class::<UnivLevelSucc>()?;
    m.add_class::<UnivLevelParam>()?;
    m.add_class::<UnivLevelMax>()?;
    m.add_class::<UnivLevelIMax>()?;
    Ok(())
}
