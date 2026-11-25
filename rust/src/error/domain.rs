//! Pure Rust domain error definitions for the poussins kernel and elaborator.
//!
//! # Architecture & Boundary Rules
//! - **Pure Data Definition Only**: This module defines ONLY the `KernelError` enum and
//!   its domain payload fields. Do NOT add PyO3 conversions, Python error codes, or
//!   user-facing message formatting here.
//! - **Pure Rust Core**: MUST NOT depend on PyO3 (`Py`, `Bound`, `PyErr`, etc.) or acquire
//!   the Python GIL.
//! - **Boundary Conversion**: Translation into Python exception classes (`KernelTypeError`,
//!   `KernelStateError`, `KernelValueError`), error codes, and formatted messages belongs
//!   exclusively in `crate::error::handler`.

use crate::ast::expr::Expr;
use crate::ast::univ_level::UnivLevel;

/// Structured domain error covering kernel typing/equality, unification,
/// and proof-state / elaborator transitions.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum KernelError {
    // KernelTypeError family
    TypeMismatch {
        expected: Expr,
        actual: Expr,
        context_expr: Option<Expr>,
    },
    DefEqMismatch {
        lhs: Expr,
        rhs: Expr,
    },
    NotAPi {
        expr: Expr,
        inferred_type: Expr,
    },
    NotASort {
        expr: Expr,
        inferred_type: Expr,
    },
    UniverseMismatch {
        lhs: UnivLevel,
        rhs: UnivLevel,
    },
    UnificationFailed {
        lhs: Expr,
        rhs: Expr,
        reason: String,
    },
    OccursCheckFailed {
        mvar_id: String,
        candidate: Expr,
    },

    // KernelStateError family
    GoalNotFound {
        goal_id: String,
    },
    MVarNotFound {
        mvar_id: String,
    },
    MVarAlreadyAssigned {
        mvar_id: String,
    },
    UnassignedMVar {
        mvar_id: String,
    },
    HypothesisNotFound {
        name: String,
        goal_id: Option<String>,
    },
    DuplicateHypothesis {
        name: String,
        goal_id: Option<String>,
    },
    InvalidProofState {
        message: String,
        goal_id: Option<String>,
    },

    // KernelValueError family
    UnboundBVar {
        idx: usize,
        context_len: usize,
    },
    UnknownFVar {
        name: String,
    },
    UnknownConstant {
        name: String,
    },
    InvalidUniverseArity {
        name: String,
        expected: usize,
        actual: usize,
    },
    InvalidValue {
        message: String,
        expr: Option<Expr>,
    },
}
