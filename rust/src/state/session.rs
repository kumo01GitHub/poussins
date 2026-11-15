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

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::*;
    use crate::ast::expr::Expr;
    use crate::state::goal::Goal;

    fn make_test_goal(id: &str) -> Goal {
        Goal::with_id(
            id,
            Expr::FVar("A".to_string()),
            HashMap::new(),
            None,
        )
    }

    #[test]
    fn test_session_initial_state() {
        let initial_snapshot = Snapshot::with_goals_and_metavars(
            vec![make_test_goal("g1")],
            HashMap::new(),
        );
        let session = Session::new(initial_snapshot);

        assert_eq!(session.history().len(), 1);
        assert!(!session.is_closed());
        assert_eq!(session.current_snapshot().goals.len(), 1);
    }

    #[test]
    fn test_session_is_closed() {
        let empty_snapshot = Snapshot::new();
        let session = Session::new(empty_snapshot);
        assert!(session.is_closed());
    }

    #[test]
    fn test_session_update_snapshot() {
        let s0 = Snapshot::with_goals_and_metavars(
            vec![make_test_goal("g1")],
            HashMap::new(),
        );
        let mut session = Session::new(s0);

        let s1 = Snapshot::with_goals_and_metavars(
            vec![make_test_goal("g2"), make_test_goal("g3")],
            HashMap::new(),
        );
        session.update_snapshot(s1);

        assert_eq!(session.history().len(), 2);
        assert_eq!(session.current_snapshot().goals.len(), 2);
        assert_eq!(session.current_snapshot().goals[0].id, "g2");
    }

    #[test]
    fn test_session_undo() {
        let s0 = Snapshot::with_goals_and_metavars(
            vec![make_test_goal("g1")],
            HashMap::new(),
        );
        let mut session = Session::new(s0);

        let s1 = Snapshot::with_goals_and_metavars(
            vec![make_test_goal("g2")],
            HashMap::new(),
        );
        session.update_snapshot(s1);

        let popped = session.undo();
        assert!(popped.is_ok());
        assert_eq!(popped.unwrap().goals[0].id, "g2");

        assert_eq!(session.history().len(), 1);
        assert_eq!(session.current_snapshot().goals[0].id, "g1");
    }

    #[test]
    fn test_session_undo_initial_fails() {
        let s0 = Snapshot::new();
        let mut session = Session::new(s0);

        let res = session.undo();
        assert_eq!(res.err(), Some(SessionError::CannotUndoInitialState));
    }
}
