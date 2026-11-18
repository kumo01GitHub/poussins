use std::collections::hash_map::DefaultHasher;
use std::collections::{HashMap, HashSet};
use std::hash::{Hash, Hasher};

use pyo3::prelude::*;
use uuid::Uuid;

use crate::ast::expr::Expr;

/// A single proof subgoal, consisting of a statement and a visible context.
///
/// The stored `context` is the merged global+local view used by the kernel,
/// while `local_hypothesis_names` tracks which entries are local binders or
/// hypotheses and may shadow globals.
#[pyclass(module = "poussins._core", eq, frozen, get_all)]
#[derive(Clone, Debug)]
pub struct Goal {
    pub id: String,
    pub statement: Expr,
    pub context: HashMap<String, Expr>,
    pub local_hypothesis_names: Option<HashSet<String>>,
}

/// Constructors for the `Goal` struct.
impl Goal {
    /// Create a new goal with a generated unique ID.
    pub fn new(
        statement: Expr,
        context: HashMap<String, Expr>,
        local_hypothesis_names: Option<HashSet<String>>,
    ) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            statement,
            context,
            local_hypothesis_names,
        }
    }

    /// Return a goal with the same identifier and context but a new statement.
    pub fn with_statement(&self, statement: Expr) -> Self {
        Self {
            id: self.id.clone(),
            statement,
            context: self.context.clone(),
            local_hypothesis_names: self.local_hypothesis_names.clone(),
        }
    }

    /// Return a goal with the same identifier and statement but a new context.
    pub fn with_context(
        &self,
        context: HashMap<String, Expr>,
        local_hypothesis_names: Option<HashSet<String>>,
    ) -> Self {
        Self {
            id: self.id.clone(),
            statement: self.statement.clone(),
            context,
            local_hypothesis_names: local_hypothesis_names
                .or_else(|| self.local_hypothesis_names.clone()),
        }
    }
}

/// Reference methods for the `Goal` struct exposed to Python.
#[pymethods]
impl Goal {
    /// Return the local hypotheses and binders in scope for this goal.
    pub fn local_context(&self) -> HashMap<String, Expr> {
        match &self.local_hypothesis_names {
            None => HashMap::new(),
            Some(names) => self
                .context
                .iter()
                .filter(|(name, _)| names.contains(*name))
                .map(|(k, v)| (k.clone(), v.clone()))
                .collect(),
        }
    }

    /// Return the visible global declarations for this goal.
    pub fn global_context(&self) -> HashMap<String, Expr> {
        match &self.local_hypothesis_names {
            None => self.context.clone(),
            Some(names) => self
                .context
                .iter()
                .filter(|(name, _)| !names.contains(*name))
                .map(|(k, v)| (k.clone(), v.clone()))
                .collect(),
        }
    }

    /// Return whether the given name belongs to the local context.
    pub fn has_local_hypothesis(&self, name: &str) -> bool {
        match &self.local_hypothesis_names {
            None => false,
            Some(names) => names.contains(name),
        }
    }

    fn __hash__(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.hash(&mut hasher);
        hasher.finish()
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