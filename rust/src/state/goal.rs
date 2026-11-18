use std::hash::{Hash, Hasher};

use pyo3::prelude::*;
use uuid::Uuid;

use crate::ast::expr::Expr;

/// A single proof subgoal, consisting of a target statement and an ordered
/// local context of hypotheses and binders.
#[pyclass(module = "poussins._core", eq, frozen, hash, get_all)]
#[derive(Clone, Debug)]
pub struct Goal {
    pub id: String,
    pub statement: Expr,
    pub local_context: Vec<(String, Expr)>,
}

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

    /// Look up the type of the most recent local hypothesis with the given name.
    pub fn lookup_local(&self, name: &str) -> Option<&Expr> {
        self.local_context
            .iter()
            .rev()
            .find(|(n, _)| n == name)
            .map(|(_, ty)| ty)
    }
}

#[pymethods]
impl Goal {
    pub fn has_local_hypothesis(&self, name: &str) -> bool {
        self.local_context.iter().any(|(n, _)| n == name)
    }

    pub fn get_local_hypothesis(&self, name: &str) -> Option<Expr> {
        self.lookup_local(name).cloned()
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
