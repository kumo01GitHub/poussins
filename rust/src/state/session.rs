use super::snapshot::Snapshot;

/// Proof session that manages the history of proof snapshots.
#[derive(Debug, Clone)]
pub struct Session {
    history: Vec<Snapshot>,
}

impl Session {
    /// Start a proof session from the given initial snapshot.
    pub fn new(initial_snapshot: Snapshot) -> Self {
        Self {
            history: vec![initial_snapshot],
        }
    }

    /// Return the current proof snapshot (the last snapshot in the history).
    pub fn current_snapshot(&self) -> &Snapshot {
        self.history
            .last()
            .expect("Session history cannot be empty")
    }

    /// Check if the proof session is closed (i.e., no active goals remain).
    pub fn is_closed(&self) -> bool {
        self.current_snapshot().is_closed()
    }

    /// Return the slice of proof snapshots in the history.
    pub fn history(&self) -> &[Snapshot] {
        &self.history
    }

    /// Update the proof session with a new snapshot, appending it to the history.
    pub fn update_snapshot(&mut self, next_snapshot: Snapshot) {
        self.history.push(next_snapshot);
    }

    pub fn undo(&mut self) -> Result<Snapshot, &'static str> {
        if self.history.len() > 1 {
            Ok(self.history.pop().unwrap())
        } else {
            Err("Cannot undo beyond the initial proof state.")
        }
    }
}
