use pyo3::prelude::*;
use pyo3::IntoPyObjectExt;

use crate::ast::expr::Expr;

/// A definition declaration in the environment.
#[pyclass(module = "poussins._core", frozen, get_all)]
#[derive(Clone, Debug)]
pub struct DefinitionDecl {
    pub name: String,
    pub ty: Expr,
    pub value: Expr,
    pub level_params: Vec<String>,
    pub mutual_decls: Vec<String>,
    pub is_opaque: bool,
}

/// An axiom declaration in the environment.
#[pyclass(module = "poussins._core", frozen, get_all)]
#[derive(Clone, Debug)]
pub struct AxiomDecl {
    pub name: String,
    pub ty: Expr,
    pub level_params: Vec<String>,
}

/// An inductive type declaration in the environment.
#[pyclass(module = "poussins._core", frozen, get_all)]
#[derive(Clone, Debug)]
pub struct InductiveDecl {
    pub name: String,
    pub ty: Expr,
    pub level_params: Vec<String>,
    pub mutual_decls: Vec<String>,
    pub constructor_names: Vec<String>,
    pub recursor_names: Vec<String>,
}

/// A constructor declaration in the environment.
#[pyclass(module = "poussins._core", frozen, get_all)]
#[derive(Clone, Debug)]
pub struct ConstructorDecl {
    pub name: String,
    pub ty: Expr,
    pub level_params: Vec<String>,
    pub inductive_name: String,
}

/// A computation rule for a recursor applied to a specific constructor.
#[pyclass(module = "poussins._core", frozen, get_all)]
#[derive(Clone, Debug)]
pub struct RecursorRule {
    pub constructor_name: String,
    pub num_fields: usize,
    pub rhs: Expr,
}

/// A recursor declaration in the environment.
#[pyclass(module = "poussins._core", frozen, get_all)]
#[derive(Clone, Debug)]
pub struct RecursorDecl {
    pub name: String,
    pub ty: Expr,
    pub level_params: Vec<String>,
    pub mutual_decls: Vec<String>,
    pub num_params: usize,
    pub num_indices: usize,
    pub num_motives: usize,
    pub num_minors: usize,
    pub rules: Vec<RecursorRule>,
}

/// Represents a declaration in the environment.
#[derive(Clone, Debug)]
pub enum Declaration {
    Definition(DefinitionDecl),
    Axiom(AxiomDecl),
    Inductive(InductiveDecl),
    Constructor(ConstructorDecl),
    Recursor(RecursorDecl),
}

impl<'py> IntoPyObject<'py> for Declaration {
    type Target = PyAny;
    type Output = Bound<'py, PyAny>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            Declaration::Definition(d) => d.into_bound_py_any(py),
            Declaration::Axiom(a) => a.into_bound_py_any(py),
            Declaration::Inductive(i) => i.into_bound_py_any(py),
            Declaration::Constructor(c) => c.into_bound_py_any(py),
            Declaration::Recursor(r) => r.into_bound_py_any(py),
        }
    }
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<DefinitionDecl>()?;
    m.add_class::<AxiomDecl>()?;
    m.add_class::<InductiveDecl>()?;
    m.add_class::<ConstructorDecl>()?;
    m.add_class::<RecursorRule>()?;
    m.add_class::<RecursorDecl>()?;
    Ok(())
}
