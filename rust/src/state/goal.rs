use std::hash::{Hash, Hasher};

use pyo3::prelude::*;
use uuid::Uuid;

use crate::ast::expr::Expr;

/// A single proof subgoal, consisting of a target statement and an ordered
/// local context of hypotheses and binders.
///
/// Global declarations live in `Environment` rather than being duplicated in
/// every goal.
#[pyclass(module = "poussins._core", eq, frozen, hash, get_all)]
#[derive(Clone, Debug)]
pub struct Goal {
    pub id: String,
    pub statement: Expr,
    pub local_context: Vec<(String, Expr)>,
}

/// Constructors and immutable update helpers for `Goal`.
impl Goal {
    /// Create a new goal with a generated unique ID.
    pub fn new(statement: Expr, local_context: Vec<(String, Expr)>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            statement,
            local_context,
        }
    }

    /// Create a new goal with an explicit ID (useful for deterministic tests).
    pub fn with_id(
        id: impl Into<String>,
        statement: Expr,
        local_context: Vec<(String, Expr)>,
    ) -> Self {
        Self {
            id: id.into(),
            statement,
            local_context,
        }
    }

    /// Return a goal with the same identifier and local context, but a new statement.
    pub fn with_statement(&self, statement: Expr) -> Self {
        Self {
            id: self.id.clone(),
            statement,
            local_context: self.local_context.clone(),
        }
    }

    /// Return a goal with the same identifier and statement, but a new local context.
    pub fn with_local_context(&self, local_context: Vec<(String, Expr)>) -> Self {
        Self {
            id: self.id.clone(),
            statement: self.statement.clone(),
            local_context,
        }
    }

    /// Look up the type of the most recent local hypothesis with the given name.
    pub fn lookup_local(&self, name: &str) -> Option<&Expr> {
        self.local_context
            .iter()
            .rev()
            .find(|(n, _)| n == name)
            .map(|(_, ty)| ty)
    }
}

/// Methods exposed to Python.
#[pymethods]
impl Goal {
    /// Return whether a local hypothesis or binder with the given name is in scope.
    pub fn has_local_hypothesis(&self, name: &str) -> bool {
        self.local_context.iter().any(|(n, _)| n == name)
    }

    /// Look up the type of the most recent local hypothesis with the given name.
    pub fn get_local_hypothesis(&self, name: &str) -> Option<Expr> {
        self.lookup_local(name).cloned()
    }

    fn __repr__(&self) -> String {
        format!("Goal(id={:?})", self.id)
    }
}

impl PartialEq for Goal {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}

impl Eq for Goal {}

impl Hash for Goal {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
    }
}
