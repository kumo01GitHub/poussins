use std::collections::HashMap;
use std::fmt;

use super::goal::Goal;
use super::metavar::MetaVar;

/// Holds the active goals list and global meta-variable instantiations at a point in time.
///
/// This acts as a pure data snapshot managing the state of an interactive proof.
#[derive(Clone, Default)]
pub struct Snapshot {
    pub goals: Vec<Goal>,
    pub metavars: HashMap<String, MetaVar>,
}

impl Snapshot {
    /// Create an empty snapshot.
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a snapshot with the given goals and metavariables.
    pub fn with_goals_and_metavars(
        goals: Vec<Goal>,
        metavars: HashMap<String, MetaVar>,
    ) -> Self {
        Self { goals, metavars }
    }

    /// Return the next active goal, if one exists.
    pub fn current_goal(&self) -> Option<&Goal> {
        self.goals.first()
    }
}

impl fmt::Debug for Snapshot {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Snapshot")
            .field("goals", &self.goals)
            .field("metavars_len", &self.metavars.len())
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ast::expr::Expr;

    fn make_test_expr(name: &str) -> Expr {
        Expr::FVar(name.to_string())
    }

    #[test]
    fn test_snapshot_current_goal() {
        let snapshot = Snapshot::new();
        assert!(snapshot.current_goal().is_none());

        let g1 = Goal::with_id("g1", make_test_expr("A"), HashMap::new(), None);
        let g2 = Goal::with_id("g2", make_test_expr("B"), HashMap::new(), None);

        let snapshot_with_goals = Snapshot::with_goals_and_metavars(
            vec![g1.clone(), g2.clone()],
            HashMap::new(),
        );

        assert_eq!(snapshot_with_goals.current_goal(), Some(&g1));
        assert_eq!(snapshot_with_goals.goals.len(), 2);
    }
}
