use crate::ast::expr::Expr;

/// Track a metavariable statement and its optional assignment.
#[derive(Debug, Clone)]
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
}
