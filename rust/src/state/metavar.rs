use std::fmt;

use crate::ast::expr::Expr;

/// Track a metavariable statement and its optional assignment.
#[derive(Clone)]
pub struct MetaVar {
    pub statement: Expr,
    pub assignment: Option<Expr>,
}

impl MetaVar {
    /// Create an unassigned metavariable with the given statement (type).
    pub fn new(statement: Expr) -> Self {
        Self {
            statement,
            assignment: None,
        }
    }

    /// Create a metavariable with the given statement and optional assignment.
    pub fn with_assignment(statement: Expr, assignment: Option<Expr>) -> Self {
        Self {
            statement,
            assignment,
        }
    }

    /// Return whether the metavariable has been assigned.
    pub fn is_assigned(&self) -> bool {
        self.assignment.is_some()
    }
}

impl fmt::Debug for MetaVar {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("MetaVar")
            .field("is_assigned", &self.is_assigned())
            .finish()
    }
}
