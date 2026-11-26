use std::collections::HashMap;
use std::sync::{Arc, RwLock};

use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;

use super::declaration::{ConstructorDecl, Declaration, RecursorDecl};

/// Pure Rust environment mapping declaration names to their kernel declarations.
#[derive(Clone, Default)]
pub struct Environment {
    declarations: HashMap<String, Declaration>,
}

impl Environment {
    /// Create a new empty environment.
    pub fn new() -> Self {
        Self::default()
    }

    pub fn has(&self, name: &str) -> bool {
        self.declarations.contains_key(name)
    }

    pub fn get(&self, name: &str) -> Option<&Declaration> {
        self.declarations.get(name)
    }

    pub fn iter(&self) -> impl Iterator<Item = (&String, &Declaration)> {
        self.declarations.iter()
    }

    pub fn len(&self) -> usize {
        self.declarations.len()
    }

    pub fn is_empty(&self) -> bool {
        self.declarations.is_empty()
    }

    /// Insert a declaration into the environment.
    pub fn insert(&mut self, name: String, declaration: Declaration) {
        self.declarations.insert(name, declaration);
    }
}

/// Python-facing shared handle to a single [`Environment`] instance.
///
/// Constructed exclusively by Rust builders/entry points (no Python `__init__`),
/// backed by `Arc<RwLock<Environment>>` so Python and Rust share one backing store.
#[pyclass(name = "Environment", module = "poussins._core", frozen)]
#[derive(Clone)]
pub struct PyEnvironment {
    inner: Arc<RwLock<Environment>>,
}

impl PyEnvironment {
    /// Wrap an existing pure-Rust [`Environment`] in a shared handle.
    pub fn from_inner(env: Environment) -> Self {
        Self {
            inner: Arc::new(RwLock::new(env)),
        }
    }

    /// Return a cloned `Arc` handle to the underlying shared environment.
    pub(crate) fn shared(&self) -> Arc<RwLock<Environment>> {
        Arc::clone(&self.inner)
    }

    fn read_guard(&self) -> PyResult<std::sync::RwLockReadGuard<'_, Environment>> {
        self.inner
            .read()
            .map_err(|_| PyRuntimeError::new_err("Environment read lock poisoned"))
    }
}

#[pymethods]
impl PyEnvironment {
    /// Check whether a declaration with `name` exists in the environment.
    pub fn has(&self, name: &str) -> PyResult<bool> {
        Ok(self.read_guard()?.has(name))
    }

    /// Return the declaration with `name`, if present.
    pub fn get(&self, name: &str) -> PyResult<Option<Declaration>> {
        Ok(self.read_guard()?.get(name).cloned())
    }

    /// Return all constructor declarations for the given inductive type name.
    pub fn get_ctors(&self, inductive_name: &str) -> PyResult<Vec<ConstructorDecl>> {
        let env = self.read_guard()?;
        let Some(Declaration::Inductive(ind)) = env.get(inductive_name) else {
            return Err(PyValueError::new_err(format!(
                "'{inductive_name}' is not a valid InductiveDeclaration."
            )));
        };
        ind.constructor_names
            .iter()
            .map(|ctor_name| match env.get(ctor_name) {
                Some(Declaration::Constructor(c)) => Ok(c.clone()),
                _ => Err(PyValueError::new_err(format!(
                    "Constructor '{ctor_name}' for inductive '{inductive_name}' is not valid."
                ))),
            })
            .collect()
    }

    /// Return all recursor declarations for the given inductive type name.
    pub fn get_recs(&self, inductive_name: &str) -> PyResult<Vec<RecursorDecl>> {
        let env = self.read_guard()?;
        let Some(Declaration::Inductive(ind)) = env.get(inductive_name) else {
            return Err(PyValueError::new_err(format!(
                "'{inductive_name}' is not a valid InductiveDeclaration."
            )));
        };
        ind.recursor_names
            .iter()
            .map(|rec_name| match env.get(rec_name) {
                Some(Declaration::Recursor(r)) => Ok(r.clone()),
                _ => Err(PyValueError::new_err(format!(
                    "Recursor '{rec_name}' for inductive '{inductive_name}' is not valid."
                ))),
            })
            .collect()
    }

    /// Return all registered declaration names.
    pub fn names(&self) -> PyResult<Vec<String>> {
        Ok(self.read_guard()?.iter().map(|(k, _)| k.clone()).collect())
    }

    fn __contains__(&self, name: &str) -> PyResult<bool> {
        self.has(name)
    }

    fn __len__(&self) -> PyResult<usize> {
        Ok(self.read_guard()?.len())
    }
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyEnvironment>()?;
    Ok(())
}
