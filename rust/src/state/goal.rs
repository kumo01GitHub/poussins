//! Proof goal representation for poussins.
//!
//! Unifies proof subgoals and metavariables into a single structure:
//! - An unassigned goal (`assignment == None`) represents an open proof obligation
//!   with target `statement` and an ordered `local_context` of accessible hypotheses/binders.
//! - An assigned goal (`assignment == Some(expr)`) holds a partial or complete proof term
//!   whose free variables are restricted to `local_context`.

use std::hash::{Hash, Hasher};

use pyo3::prelude::*;
use uuid::Uuid;

use crate::ast::expr::Expr;

/// A single proof goal, consisting of a target statement, an ordered local context
/// of hypotheses and binders, and an optional proof-term assignment.
#[pyclass(module = "poussins._core", eq, frozen, hash, get_all)]
#[derive(Clone, Debug)]
pub struct Goal {
    pub id: String,
    pub statement: Expr,
    pub local_context: Vec<(String, Expr)>,
    pub assignment: Option<Expr>,
}

impl Goal {
    /// Create a new unassigned goal with a generated unique ID.
    pub fn new(statement: Expr, local_context: Vec<(String, Expr)>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            statement,
            local_context,
            assignment: None,
        }
    }

    /// Create a new unassigned goal with an explicit ID (useful for deterministic tests).
    pub fn with_id(
        id: impl Into<String>,
        statement: Expr,
        local_context: Vec<(String, Expr)>,
    ) -> Self {
        Self {
            id: id.into(),
            statement,
            local_context,
            assignment: None,
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
    pub fn is_closed(&self) -> bool {
        self.assignment.is_some()
    }

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
