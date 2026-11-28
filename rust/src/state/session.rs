//! Proof session managing the chronological history of immutable [`Snapshot`] states.
//!
//! Role separation with `ProofManager`:
//! - `Session` is a pure Rust history container enforcing `history.len() >= 1`
//!   (the initial snapshot is never popped).
//! - `ProofManager` owns the transaction boundary: it runs `engine` transitions
//!   against `Environment`, commits valid next snapshots via `update_snapshot`
//!   (leaving `Session` untouched on failure), and exposes the PyO3 interface.

use crate::error::KernelError;
use crate::state::snapshot::Snapshot;

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

    /// Update the proof session with a new snapshot, appending it to the history.
    pub fn update_snapshot(&mut self, next_snapshot: Snapshot) {
        self.history.push(next_snapshot);
    }

    /// Revert to the previous snapshot, returning the popped snapshot.
    ///
    /// Fails if already at the initial proof state (`history.len() == 1`).
    pub fn undo(&mut self) -> Result<Snapshot, KernelError> {
        if self.history.len() > 1 {
            Ok(self.history.pop().unwrap())
        } else {
            Err(KernelError::InvalidValue {
                message: "Cannot undo beyond the initial proof state.".to_string(),
                expr: None,
            })
        }
    }

    /// Return the number of snapshots recorded in history (always `>= 1`).
    pub fn len(&self) -> usize {
        self.history.len()
    }
}
