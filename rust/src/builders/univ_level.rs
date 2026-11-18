/// Builder functions for constructing universe levels.
///
/// This module provides ergonomic universe-level constructors, matching the
/// Python-side builder style while keeping universe logic separate from
/// expression builders.
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyTuple};

use crate::ast::univ_level::UnivLevel;

/// Input type for universe-level builders (usable from both Rust and Python).
pub enum UnivLevelInput {
    Int(i64),
    Param(String),
    Level(UnivLevel),
}

impl From<i64> for UnivLevelInput {
    fn from(n: i64) -> Self {
        Self::Int(n)
    }
}

impl From<String> for UnivLevelInput {
    fn from(s: String) -> Self {
        Self::Param(s)
    }
}

impl From<&str> for UnivLevelInput {
    fn from(s: &str) -> Self {
        Self::Param(s.to_string())
    }
}

impl From<UnivLevel> for UnivLevelInput {
    fn from(level: UnivLevel) -> Self {
        Self::Level(level)
    }
}

impl<'a, 'py> FromPyObject<'a, 'py> for UnivLevelInput {
    type Error = PyErr;

    fn extract(ob: Borrowed<'a, 'py, PyAny>) -> PyResult<Self> {
        if let Ok(n) = ob.extract::<i64>() {
            Ok(Self::Int(n))
        } else if let Ok(s) = ob.extract::<String>() {
            Ok(Self::Param(s))
        } else if let Ok(lvl) = ob.extract::<UnivLevel>() {
            Ok(Self::Level(lvl))
        } else {
            let name = ob.get_type().name()?;
            Err(PyTypeError::new_err(format!(
                "Expected int, str, or UnivLevel, got {}",
                name
            )))
        }
    }
}

/// Try to build a universe level from input, returning an error if an integer is negative.
pub fn try_build_univ_level(level: UnivLevelInput) -> PyResult<UnivLevel> {
    match level {
        UnivLevelInput::Int(n) => {
            if n < 0 {
                return Err(PyValueError::new_err(format!(
                    "Universe level must be non-negative, got {}",
                    n
                )));
            }
            let mut result = UnivLevel::Zero;
            for _ in 0..n {
                result = UnivLevel::Succ(Box::new(result));
            }
            Ok(result)
        }
        UnivLevelInput::Param(name) => Ok(UnivLevel::Param(name)),
        UnivLevelInput::Level(level) => Ok(level),
    }
}

/// Build a universe level from Rust input (panics on negative integer).
pub fn build_univ_level(level: UnivLevelInput) -> UnivLevel {
    try_build_univ_level(level).unwrap_or_else(|e| panic!("{}", e))
}

/// Build multiple universe levels from Rust inputs.
pub fn build_univ_levels(levels: impl IntoIterator<Item = UnivLevelInput>) -> Vec<UnivLevel> {
    levels.into_iter().map(build_univ_level).collect()
}

/// Build a `max` universe level from Rust inputs.
pub fn build_univ_level_max(levels: impl IntoIterator<Item = UnivLevelInput>) -> UnivLevel {
    let mut iter = levels.into_iter();
    let first = iter
        .next()
        .unwrap_or_else(|| panic!("univ_level_max requires at least one level."));
    let mut result = build_univ_level(first);
    for level in iter {
        result = UnivLevel::Max(Box::new(result), Box::new(build_univ_level(level)));
    }
    result
}

/// Build an `imax` universe level from two Rust inputs.
pub fn build_univ_level_imax(left: UnivLevelInput, right: UnivLevelInput) -> UnivLevel {
    UnivLevel::IMax(
        Box::new(build_univ_level(left)),
        Box::new(build_univ_level(right)),
    )
}

// -------------------------------------------------------------------------
// Python bindings
// -------------------------------------------------------------------------

/// Build a universe level from an integer, string, or existing `UnivLevel`.
#[pyfunction]
pub fn univ_level(level: UnivLevelInput) -> PyResult<UnivLevel> {
    try_build_univ_level(level)
}

/// Build multiple universe levels from a sequence of level inputs.
#[pyfunction]
pub fn univ_levels(levels: &Bound<'_, PyAny>) -> PyResult<Py<PyTuple>> {
    let py = levels.py();
    let mut out = Vec::new();
    for item in levels.try_iter()? {
        let input: UnivLevelInput = item?.extract()?;
        out.push(try_build_univ_level(input)?);
    }
    Ok(PyTuple::new(py, out)?.unbind())
}

/// Build a `max` universe level from one or more inputs.
#[pyfunction]
#[pyo3(signature = (*levels))]
pub fn univ_level_max(levels: &Bound<'_, PyTuple>) -> PyResult<UnivLevel> {
    if levels.is_empty() {
        return Err(PyValueError::new_err(
            "univ_level_max requires at least one level.",
        ));
    }
    let mut iter = levels.iter();
    let mut result = try_build_univ_level(iter.next().unwrap().extract()?)?;
    for item in iter {
        let next_lvl = try_build_univ_level(item.extract()?)?;
        result = UnivLevel::Max(Box::new(result), Box::new(next_lvl));
    }
    Ok(result)
}

/// Build an `imax` universe level from two inputs.
#[pyfunction]
pub fn univ_level_imax(left: UnivLevelInput, right: UnivLevelInput) -> PyResult<UnivLevel> {
    Ok(UnivLevel::IMax(
        Box::new(try_build_univ_level(left)?),
        Box::new(try_build_univ_level(right)?),
    ))
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(univ_level, m)?)?;
    m.add_function(wrap_pyfunction!(univ_levels, m)?)?;
    m.add_function(wrap_pyfunction!(univ_level_max, m)?)?;
    m.add_function(wrap_pyfunction!(univ_level_imax, m)?)?;
    Ok(())
}