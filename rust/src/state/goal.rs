use std::collections::{HashMap, HashSet};
use std::fmt;
use std::hash::{Hash, Hasher};
use std::sync::atomic::{AtomicU64, Ordering};

use crate::ast::expr::Expr;

static GOAL_ID_COUNTER: AtomicU64 = AtomicU64::new(1);

fn next_goal_id() -> String {
    let id = GOAL_ID_COUNTER.fetch_add(1, Ordering::Relaxed);
    format!("goal_{}", id)
}

/// A single proof subgoal, consisting of a statement and a visible context.
///
/// The stored `context` is the merged global+local view used by the kernel,
/// while `local_hypothesis_names` tracks which entries are local binders or
/// hypotheses and may shadow globals.
#[derive(Clone)]
pub struct Goal {
    pub id: String,
    pub statement: Expr,
    pub context: HashMap<String, Expr>,
    pub local_hypothesis_names: Option<HashSet<String>>,
}

impl Goal {
    /// Create a new goal with a generated unique ID.
    pub fn new(
        statement: Expr,
        context: HashMap<String, Expr>,
        local_hypothesis_names: Option<HashSet<String>>,
    ) -> Self {
        Self {
            id: next_goal_id(),
            statement,
            context,
            local_hypothesis_names,
        }
    }

    /// Create a new goal with a specific ID.
    pub fn with_id(
        id: impl Into<String>,
        statement: Expr,
        context: HashMap<String, Expr>,
        local_hypothesis_names: Option<HashSet<String>>,
    ) -> Self {
        Self {
            id: id.into(),
            statement,
            context,
            local_hypothesis_names,
        }
    }

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

impl fmt::Debug for Goal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Goal")
            .field("id", &self.id)
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ast::univ_level::UnivLevel;

    fn make_test_expr(name: &str) -> Expr {
        Expr::FVar(name.to_string())
    }

    #[test]
    fn test_goal_creation_and_id_uniqueness() {
        let g1 = Goal::new(make_test_expr("A"), HashMap::new(), None);
        let g2 = Goal::new(make_test_expr("A"), HashMap::new(), None);
        assert_ne!(g1.id, g2.id);
        assert_ne!(g1, g2);
    }

    #[test]
    fn test_goal_equality_by_id() {
        let g1 = Goal::with_id("g1", make_test_expr("A"), HashMap::new(), None);
        let g2 = Goal::with_id("g1", make_test_expr("B"), HashMap::new(), None);
        assert_eq!(g1, g2);
    }

    #[test]
    fn test_local_and_global_context() {
        let mut context = HashMap::new();
        context.insert("glob".to_string(), make_test_expr("Type"));
        context.insert("loc".to_string(), make_test_expr("Prop"));

        let mut locals = HashSet::new();
        locals.insert("loc".to_string());

        let goal = Goal::new(
            Expr::Sort(UnivLevel::Zero),
            context,
            Some(locals),
        );

        assert!(goal.has_local_hypothesis("loc"));
        assert!(!goal.has_local_hypothesis("glob"));
        assert!(!goal.has_local_hypothesis("unknown"));

        let local_ctx = goal.local_context();
        assert_eq!(local_ctx.len(), 1);
        assert!(local_ctx.contains_key("loc"));

        let global_ctx = goal.global_context();
        assert_eq!(global_ctx.len(), 1);
        assert!(global_ctx.contains_key("glob"));
    }

    #[test]
    fn test_with_statement() {
        let goal = Goal::with_id("test_id", make_test_expr("A"), HashMap::new(), None);
        let updated = goal.with_statement(make_test_expr("B"));
        assert_eq!(updated.id, "test_id");
        assert_eq!(goal, updated);
    }

    #[test]
    fn test_with_context() {
        let mut ctx1 = HashMap::new();
        ctx1.insert("x".to_string(), make_test_expr("A"));
        let goal = Goal::with_id("test_id", make_test_expr("A"), ctx1, None);

        let mut ctx2 = HashMap::new();
        ctx2.insert("y".to_string(), make_test_expr("B"));
        let updated = goal.with_context(ctx2, None);

        assert_eq!(updated.id, "test_id");
        assert!(updated.context.contains_key("y"));
        assert!(!updated.context.contains_key("x"));
    }
}
