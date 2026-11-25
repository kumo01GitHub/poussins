//! PyO3 exception boundary handler for `KernelError`.
//!
//! # Architecture & Boundary Rules
//! - **Boundary Only**: This module is the ONLY place where `KernelError` is translated
//!   into Python exceptions (`PyErr`), human-readable messages, and machine-readable error
//!   codes. Core Rust modules must never import this module directly.
//! - **Structured Python Inspection**: Attaches `code` and relevant AST/identifier attributes
//!   directly onto the raised `KernelTypeError` / `KernelStateError` / `KernelValueError`
//!   instance so Python callers can inspect failure locations programmatically.

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use crate::error::domain::KernelError;

impl From<KernelError> for PyErr {
    fn from(err: KernelError) -> PyErr {
        Python::attach(|py| build_py_err(py, err))
    }
}

fn build_py_err(py: Python<'_>, err: KernelError) -> PyErr {
    let class_name = exception_class_name(&err);
    let message = format_message(&err);

    let Ok(errors_mod) = py.import("poussins.errors") else {
        return PyRuntimeError::new_err(message);
    };
    let Ok(cls) = errors_mod.getattr(class_name) else {
        return PyRuntimeError::new_err(message);
    };
    let Ok(exc_inst) = cls.call1((message.clone(),)) else {
        return PyRuntimeError::new_err(message);
    };

    let _ = exc_inst.setattr("code", error_code(&err));
    attach_structured_fields(&exc_inst, &err);

    PyErr::from_value(exc_inst)
}

fn exception_class_name(err: &KernelError) -> &'static str {
    match err {
        KernelError::TypeMismatch { .. }
        | KernelError::DefEqMismatch { .. }
        | KernelError::NotAPi { .. }
        | KernelError::NotASort { .. }
        | KernelError::UniverseMismatch { .. }
        | KernelError::UnificationFailed { .. }
        | KernelError::OccursCheckFailed { .. } => "KernelTypeError",

        KernelError::GoalNotFound { .. }
        | KernelError::MVarNotFound { .. }
        | KernelError::MVarAlreadyAssigned { .. }
        | KernelError::UnassignedMVar { .. }
        | KernelError::HypothesisNotFound { .. }
        | KernelError::DuplicateHypothesis { .. }
        | KernelError::InvalidProofState { .. } => "KernelStateError",

        KernelError::UnboundBVar { .. }
        | KernelError::UnknownFVar { .. }
        | KernelError::UnknownConstant { .. }
        | KernelError::InvalidUniverseArity { .. }
        | KernelError::InvalidValue { .. } => "KernelValueError",
    }
}

fn error_code(err: &KernelError) -> &'static str {
    match err {
        KernelError::TypeMismatch { .. } => "type_mismatch",
        KernelError::DefEqMismatch { .. } => "def_eq_mismatch",
        KernelError::NotAPi { .. } => "not_a_pi",
        KernelError::NotASort { .. } => "not_a_sort",
        KernelError::UniverseMismatch { .. } => "universe_mismatch",
        KernelError::UnificationFailed { .. } => "unification_failed",
        KernelError::OccursCheckFailed { .. } => "occurs_check_failed",
        KernelError::GoalNotFound { .. } => "goal_not_found",
        KernelError::MVarNotFound { .. } => "mvar_not_found",
        KernelError::MVarAlreadyAssigned { .. } => "mvar_already_assigned",
        KernelError::UnassignedMVar { .. } => "unassigned_mvar",
        KernelError::HypothesisNotFound { .. } => "hypothesis_not_found",
        KernelError::DuplicateHypothesis { .. } => "duplicate_hypothesis",
        KernelError::InvalidProofState { .. } => "invalid_proof_state",
        KernelError::UnboundBVar { .. } => "unbound_bvar",
        KernelError::UnknownFVar { .. } => "unknown_fvar",
        KernelError::UnknownConstant { .. } => "unknown_constant",
        KernelError::InvalidUniverseArity { .. } => "invalid_universe_arity",
        KernelError::InvalidValue { .. } => "invalid_value",
    }
}

fn format_message(err: &KernelError) -> String {
    match err {
        KernelError::TypeMismatch { expected, actual, .. } => {
            format!("Type mismatch: expected {expected:?}, got {actual:?}")
        }
        KernelError::DefEqMismatch { lhs, rhs } => {
            format!("Expressions are not definitionally equal: {lhs:?} vs {rhs:?}")
        }
        KernelError::NotAPi { inferred_type, .. } => {
            format!("Expected Pi type, got {inferred_type:?}")
        }
        KernelError::NotASort { inferred_type, .. } => {
            format!("Expected Sort, got {inferred_type:?}")
        }
        KernelError::UniverseMismatch { lhs, rhs } => {
            format!("Universe level mismatch: {lhs:?} vs {rhs:?}")
        }
        KernelError::UnificationFailed { lhs, rhs, reason } => {
            format!("Unification failed between {lhs:?} and {rhs:?}: {reason}")
        }
        KernelError::OccursCheckFailed { mvar_id, candidate } => {
            format!("Occurs check failed for ?{mvar_id} in {candidate:?}")
        }
        KernelError::GoalNotFound { goal_id } => format!("Goal not found: {goal_id}"),
        KernelError::MVarNotFound { mvar_id } => format!("Metavariable not found: ?{mvar_id}"),
        KernelError::MVarAlreadyAssigned { mvar_id } => {
            format!("Metavariable ?{mvar_id} is already assigned")
        }
        KernelError::UnassignedMVar { mvar_id } => format!("Metavariable ?{mvar_id} is unassigned"),
        KernelError::HypothesisNotFound { name, goal_id } => match goal_id {
            Some(gid) => format!("Hypothesis '{name}' not found in goal {gid}"),
            None => format!("Hypothesis '{name}' not found"),
        },
        KernelError::DuplicateHypothesis { name, goal_id } => match goal_id {
            Some(gid) => format!("Duplicate hypothesis '{name}' in goal {gid}"),
            None => format!("Duplicate hypothesis '{name}'"),
        },
        KernelError::InvalidProofState { message, .. } => format!("Invalid proof state: {message}"),
        KernelError::UnboundBVar { idx, context_len } => {
            format!("Unbound bound variable #{idx} (context length: {context_len})")
        }
        KernelError::UnknownFVar { name } => format!("Unknown free variable: {name}"),
        KernelError::UnknownConstant { name } => format!("Unknown constant: {name}"),
        KernelError::InvalidUniverseArity { name, expected, actual } => {
            format!("Invalid universe level count for '{name}': expected {expected}, got {actual}")
        }
        KernelError::InvalidValue { message, .. } => format!("Invalid value: {message}"),
    }
}

fn attach_structured_fields(exc: &Bound<'_, PyAny>, err: &KernelError) {
    match err {
        KernelError::TypeMismatch {
            expected,
            actual,
            context_expr,
        } => {
            let _ = exc.setattr("expected", expected.clone());
            let _ = exc.setattr("actual", actual.clone());
            let _ = exc.setattr("expr", context_expr.clone());
        }
        KernelError::DefEqMismatch { lhs, rhs } => {
            let _ = exc.setattr("lhs", lhs.clone());
            let _ = exc.setattr("rhs", rhs.clone());
        }
        KernelError::NotAPi {
            expr,
            inferred_type,
        }
        | KernelError::NotASort {
            expr,
            inferred_type,
        } => {
            let _ = exc.setattr("expr", expr.clone());
            let _ = exc.setattr("inferred_type", inferred_type.clone());
        }
        KernelError::UniverseMismatch { lhs, rhs } => {
            let _ = exc.setattr("lhs", lhs.clone());
            let _ = exc.setattr("rhs", rhs.clone());
        }
        KernelError::UnificationFailed { lhs, rhs, .. } => {
            let _ = exc.setattr("lhs", lhs.clone());
            let _ = exc.setattr("rhs", rhs.clone());
        }
        KernelError::OccursCheckFailed { mvar_id, candidate } => {
            let _ = exc.setattr("mvar_id", mvar_id.as_str());
            let _ = exc.setattr("expr", candidate.clone());
        }
        KernelError::GoalNotFound { goal_id } => {
            let _ = exc.setattr("goal_id", goal_id.as_str());
        }
        KernelError::MVarNotFound { mvar_id }
        | KernelError::MVarAlreadyAssigned { mvar_id }
        | KernelError::UnassignedMVar { mvar_id } => {
            let _ = exc.setattr("mvar_id", mvar_id.as_str());
        }
        KernelError::HypothesisNotFound { name, goal_id }
        | KernelError::DuplicateHypothesis { name, goal_id } => {
            let _ = exc.setattr("name", name.as_str());
            let _ = exc.setattr("goal_id", goal_id.as_deref());
        }
        KernelError::InvalidProofState { goal_id, .. } => {
            let _ = exc.setattr("goal_id", goal_id.as_deref());
        }
        KernelError::UnboundBVar { idx, context_len } => {
            let _ = exc.setattr("idx", *idx);
            let _ = exc.setattr("context_len", *context_len);
        }
        KernelError::UnknownFVar { name } | KernelError::UnknownConstant { name } => {
            let _ = exc.setattr("name", name.as_str());
        }
        KernelError::InvalidUniverseArity {
            name,
            expected,
            actual,
        } => {
            let _ = exc.setattr("name", name.as_str());
            let _ = exc.setattr("expected", *expected);
            let _ = exc.setattr("actual", *actual);
        }
        KernelError::InvalidValue { expr, .. } => {
            let _ = exc.setattr("expr", expr.clone());
        }
    }
}
