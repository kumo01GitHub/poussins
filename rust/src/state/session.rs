use std::fmt;

use super::snapshot::Snapshot;

/// Error when attempting an invalid session operation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SessionError {
    CannotUndoInitialState,
}

impl fmt::Display for SessionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::CannotUndoInitialState => {
                write!(f, "Cannot undo beyond the initial proof state.")
            }
        }
    }
}

impl std::error::Error for SessionError {}

/// Proof session that manages the history of proof snapshots.
#[derive(Clone)]
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
        self.current_snapshot().goals.is_empty()
    }

    /// Return the slice of proof snapshots in the history.
    pub fn history(&self) -> &[Snapshot] {
        &self.history
    }

    /// Update the proof session with a new snapshot, appending it to the history.
    pub fn update_snapshot(&mut self, next_snapshot: Snapshot) {
        self.history.push(next_snapshot);
    }

    /// Undo the last proof snapshot, reverting to the previous snapshot in the history.
    pub fn undo(&mut self) -> Result<Snapshot, SessionError> {
        if self.history.len() > 1 {
            Ok(self.history.pop().unwrap())
        } else {
            Err(SessionError::CannotUndoInitialState)
        }
    }
}

impl fmt::Debug for Session {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Session")
            .field("history_len", &self.history.len())
            .field("is_closed", &self.is_closed())
            .finish()
    }
}
