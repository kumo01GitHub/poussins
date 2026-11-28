//! Proof manager coordinating `Session` and `engine` transitions for
//! interactive proof construction.

use std::sync::{Arc, RwLock};

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use crate::ast::expr::Expr;
use crate::elaborator::calc::instantiate_mvars_arc;
use crate::elaborator::engine::{
    change as engine_change, close_goal as engine_close_goal,
    create_initial_snapshot as engine_create_initial_snapshot,
    refine_goal as engine_refine_goal,
};
use crate::environment::environment::{Environment, PyEnvironment};
use crate::error::KernelError;
use crate::state::goal::Goal;
use crate::state::session::Session;

fn read_env(env: &Arc<RwLock<Environment>>) -> PyResult<std::sync::RwLockReadGuard<'_, Environment>> {
    env.read()
        .map_err(|_| PyRuntimeError::new_err("Environment read lock poisoned"))
}

/// Interactive proof session manager owning [`Session`] history and driving
/// validated state transitions via `engine` against a shared [`Environment`].
#[pyclass(name = "ProofManager")]
pub struct ProofManager {
    session: Session,
    env: Arc<RwLock<Environment>>,
}

impl ProofManager {
    /// Internal Rust constructor from an already-constructed [`Session`] and shared [`Environment`].
    pub(crate) fn from_session(session: Session, env: Arc<RwLock<Environment>>) -> Self {
        Self { session, env }
    }

    /// Borrow the active [`Session`] (for internal Rust callers / tests).
    pub(crate) fn session(&self) -> &Session {
        &self.session
    }

    /// Return a cloned handle to the shared [`Environment`].
    pub(crate) fn shared_env(&self) -> Arc<RwLock<Environment>> {
        Arc::clone(&self.env)
    }

    /// Reconstruct the current proof term by instantiating metavariables from the
    /// initial goal assignment in the current snapshot.
    pub fn build_current_term(&self) -> Result<Expr, KernelError> {
        let snapshot = self.session.current_snapshot();
        let Some(root_goal) = snapshot.goals.get("0") else {
            return Err(KernelError::InvalidValue {
                message: "Initial goal '?0' is missing from snapshot.".to_string(),
                expr: None,
            });
        };
        let Some(assignment) = &root_goal.assignment else {
            return Err(KernelError::InvalidValue {
                message: "Proof is not complete yet: initial goal is unassigned.".to_string(),
                expr: None,
            });
        };
        let instantiated = instantiate_mvars_arc(&Arc::new(assignment.clone()), snapshot)?;
        Ok(Arc::try_unwrap(instantiated).unwrap_or_else(|a| (*a).clone()))
    }
}

#[pymethods]
impl ProofManager {
    /// Start a proof for `statement` under `env`.
    #[new]
    pub fn new(statement: Expr, env: &PyEnvironment) -> PyResult<Self> {
        let shared_env = env.shared();
        let initial_snapshot = {
            let env_guard = read_env(&shared_env)?;
            engine_create_initial_snapshot(statement, &env_guard)?
        };
        Ok(Self {
            session: Session::new(initial_snapshot),
            env: shared_env,
        })
    }

    /// Return the current active [`Goal`], or `None` if all goals are closed.
    pub fn current_goal(&self) -> Option<Goal> {
        self.session.current_snapshot().current_goal().cloned()
    }

    /// Return `true` if all goals in the current snapshot are closed.
    pub fn is_closed(&self) -> bool {
        self.session.is_closed()
    }

    /// Return the number of snapshots stored in undo history (always >= 1).
    pub fn history_len(&self) -> usize {
        self.session.len()
    }

    /// Close the current active goal with a complete `assignment` expression.
    pub fn close_goal(&mut self, assignment: Expr) -> PyResult<()> {
        let next = {
            let env_guard = read_env(&self.env)?;
            engine_close_goal(self.session.current_snapshot(), assignment, &env_guard)?
        };
        self.session.update_snapshot(next);
        Ok(())
    }

    /// Refine the current active goal with `assignment` and ordered `subgoals`.
    pub fn refine_goal(
        &mut self,
        assignment: Expr,
        subgoals: Vec<PyRef<'_, Goal>>,
    ) -> PyResult<()> {
        let owned_subgoals: Vec<Goal> = subgoals.into_iter().map(|g| (*g).clone()).collect();
        let next = {
            let env_guard = read_env(&self.env)?;
            engine_refine_goal(
                self.session.current_snapshot(),
                assignment,
                owned_subgoals,
                &env_guard,
            )?
        };
        self.session.update_snapshot(next);
        Ok(())
    }

    /// Replace the current goal statement and/or local hypothesis types with
    /// definitionally equal expressions in a single step.
    #[pyo3(signature = (new_statement=None, hypothesis_updates=None))]
    pub fn change(
        &mut self,
        new_statement: Option<Expr>,
        hypothesis_updates: Option<Vec<(String, Expr)>>,
    ) -> PyResult<()> {
        let updates = hypothesis_updates.unwrap_or_default();
        let next = {
            let env_guard = read_env(&self.env)?;
            engine_change(
                self.session.current_snapshot(),
                new_statement,
                &updates,
                &env_guard,
            )?
        };
        self.session.update_snapshot(next);
        Ok(())
    }

    /// Revert the last proof transition.
    pub fn undo(&mut self) -> PyResult<()> {
        self.session.undo()?;
        Ok(())
    }

    /// Reconstruct and return the current proof term once all goals are closed.
    pub fn current_term(&self) -> PyResult<Expr> {
        Ok(self.build_current_term()?)
    }
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ProofManager>()?;
    Ok(())
}
