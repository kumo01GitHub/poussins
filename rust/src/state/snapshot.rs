use std::collections::HashMap;

use super::goal::Goal;
use super::metavar::MetaVar;

/// Holds the active goals list and global meta-variable instantiations at a point in time.
#[derive(Debug, Clone, Default)]
pub struct Snapshot {
    pub goals: Vec<Goal>,
    pub metavars: HashMap<String, MetaVar>,
}

impl Snapshot {
    pub fn new(goals: Vec<Goal>, metavars: HashMap<String, MetaVar>) -> Self {
        Self { goals, metavars }
    }

    /// Check if the snapshot has no active goals.
    pub fn is_closed(&self) -> bool {
        self.goals.is_empty()
    }
}
