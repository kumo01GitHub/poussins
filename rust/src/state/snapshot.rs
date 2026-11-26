//! Proof state snapshot representation for poussins.
//!
//! Stores all proof goals (both open obligations and partially/fully assigned
//! proof terms) in a single map alongside the ordered queue of active goal IDs.

use std::collections::HashMap;

use crate::ast::expr::Expr;

use super::goal::Goal;

/// Holds all proof goals and the ordered queue of active goal IDs at a point in time.
#[derive(Debug, Clone, Default)]
pub struct Snapshot {
    /// All goals (open, intermediate, and closed) indexed by their unique ID.
    pub goals: HashMap<String, Goal>,
    /// Ordered list of active (unassigned) goal IDs presented to the user/tactics.
    pub goal_queue: Vec<String>,
}

impl Snapshot {
    /// Create a snapshot from an explicit goal map and active queue.
    pub fn new(goals: HashMap<String, Goal>, goal_queue: Vec<String>) -> Self {
        Self { goals, goal_queue }
    }

    /// Create a snapshot initialized with a single root goal.
    pub fn with_root(root: Goal) -> Self {
        let id = root.id.clone();
        let mut goals = HashMap::new();
        goals.insert(id.clone(), root);
        Self {
            goals,
            goal_queue: vec![id],
        }
    }

    /// Look up a goal by ID.
    pub fn get_goal(&self, id: &str) -> Option<&Goal> {
        self.goals.get(id)
    }

    /// Look up a mutable goal by ID.
    pub fn get_goal_mut(&mut self, id: &str) -> Option<&mut Goal> {
        self.goals.get_mut(id)
    }

    /// Register a new goal and append its ID to the end of `goal_queue` if unassigned.
    pub fn push_goal(&mut self, goal: Goal) {
        let id = goal.id.clone();
        let is_open = !goal.is_closed();
        self.goals.insert(id.clone(), goal);
        if is_open && !self.goal_queue.iter().any(|existing| existing == &id) {
            self.goal_queue.push(id);
        }
    }

    /// Register a new goal and insert its ID at `index` in `goal_queue` if unassigned.
    pub fn insert_goal(&mut self, index: usize, goal: Goal) {
        let id = goal.id.clone();
        let is_open = !goal.is_closed();
        self.goals.insert(id.clone(), goal);
        if is_open && !self.goal_queue.iter().any(|existing| existing == &id) {
            let pos = index.min(self.goal_queue.len());
            self.goal_queue.insert(pos, id);
        }
    }

    /// Assign a proof term to the goal with `id` and remove it from `goal_queue`.
    ///
    /// Returns `true` if the goal existed and was updated, `false` if `id` was not found.
    pub fn assign(&mut self, id: &str, expr: Expr) -> bool {
        let Some(goal) = self.goals.get_mut(id) else {
            return false;
        };
        goal.assignment = Some(expr);
        self.goal_queue.retain(|queued_id| queued_id != id);
        true
    }

    /// Return the first active (unassigned) goal in `goal_queue`, if any.
    pub fn current_goal(&self) -> Option<&Goal> {
        self.goal_queue
            .iter()
            .filter_map(|id| self.goals.get(id))
            .find(|g| !g.is_closed())
    }

    /// Return all active (unassigned) goals in `goal_queue` order.
    pub fn active_goals(&self) -> Vec<&Goal> {
        self.goal_queue
            .iter()
            .filter_map(|id| self.goals.get(id))
            .filter(|g| !g.is_closed())
            .collect()
    }

    /// Check whether all goals in the snapshot are closed (assigned) and no active goals remain.
    pub fn is_closed(&self) -> bool {
        self.goal_queue.is_empty() && self.goals.values().all(Goal::is_closed)
    }
}
