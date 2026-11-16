/// Builder functions for constructing universe levels.
///
/// This module provides ergonomic universe-level constructors, matching the
/// Python-side builder style while keeping universe logic separate from
/// expression builders.

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyTuple};

use crate::ast::univ_level::UnivLevel;

pub fn extract_univ_level(obj: &Bound<'_, PyAny>) -> PyResult<UnivLevel> {
    if let Ok(n) = obj.extract::<i64>() {
        if n < 0 {
            return Err(PyValueError::new_err(
                "Universe level must be non-negative.",
            ));
        }
        let mut result = UnivLevel::Zero;
        for _ in 0..n {
            result = UnivLevel::Succ(Box::new(result));
        }
        return Ok(result);
    }

    if let Ok(s) = obj.extract::<String>() {
        return Ok(UnivLevel::Param(s));
    }

    let type_name = obj.get_type().name()?;
    let name_str = type_name.to_str()?;
    match name_str {
        "UnivLevelZero" => Ok(UnivLevel::Zero),
        "UnivLevelSucc" => {
            let pred = obj.getattr("pred")?;
            Ok(UnivLevel::Succ(Box::new(extract_univ_level(&pred)?)))
        }
        "UnivLevelParam" => {
            let name: String = obj.getattr("name")?.extract()?;
            Ok(UnivLevel::Param(name))
        }
        "UnivLevelMax" => {
            let left = obj.getattr("left")?;
            let right = obj.getattr("right")?;
            Ok(UnivLevel::Max(
                Box::new(extract_univ_level(&left)?),
                Box::new(extract_univ_level(&right)?),
            ))
        }
        "UnivLevelIMax" => {
            let left = obj.getattr("left")?;
            let right = obj.getattr("right")?;
            Ok(UnivLevel::IMax(
                Box::new(extract_univ_level(&left)?),
                Box::new(extract_univ_level(&right)?),
            ))
        }
        _ => Err(PyTypeError::new_err(format!(
            "Expected int, str, or UnivLevel, got {}",
            name_str
        ))),
    }
}

/// Build a universe level from an integer, string, or existing `UnivLevel`.
#[pyfunction]
#[pyo3(signature = (level))]
pub fn univ_level(py: Python<'_>, level: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let lvl = extract_univ_level(level)?;
    lvl.into_pyobject(py).map(|obj| obj.unbind())
}

/// Build multiple universe levels from a sequence of level inputs.
#[pyfunction]
#[pyo3(signature = (levels))]
pub fn univ_levels(py: Python<'_>, levels: &Bound<'_, PyAny>) -> PyResult<Py<PyTuple>> {
    let mut py_levels = Vec::new();
    for item in levels.try_iter()? {
        let item = item?;
        let lvl = extract_univ_level(&item)?;
        let py_obj = lvl.into_pyobject(py).map(|obj| obj.unbind())?;
        py_levels.push(py_obj);
    }
    Ok(PyTuple::new(py, py_levels)?.unbind())
}

/// Build a `max` universe level from one or more inputs.
#[pyfunction]
#[pyo3(signature = (*levels))]
pub fn univ_level_max(py: Python<'_>, levels: &Bound<'_, PyTuple>) -> PyResult<Py<PyAny>> {
    if levels.is_empty() {
        return Err(PyValueError::new_err(
            "univ_level_max requires at least one level.",
        ));
    }
    let mut iter = levels.iter();
    let first = iter.next().unwrap();
    let mut result = extract_univ_level(&first)?;
    for item in iter {
        let next_lvl = extract_univ_level(&item)?;
        result = UnivLevel::Max(Box::new(result), Box::new(next_lvl));
    }
    result.into_pyobject(py).map(|obj| obj.unbind())
}

/// Build an `imax` universe level from two inputs.
#[pyfunction]
#[pyo3(signature = (left, right))]
pub fn univ_level_imax(
    py: Python<'_>,
    left: &Bound<'_, PyAny>,
    right: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    let left_lvl = extract_univ_level(left)?;
    let right_lvl = extract_univ_level(right)?;
    let res = UnivLevel::IMax(Box::new(left_lvl), Box::new(right_lvl));
    res.into_pyobject(py).map(|obj| obj.unbind())
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(univ_level, m)?)?;
    m.add_function(wrap_pyfunction!(univ_levels, m)?)?;
    m.add_function(wrap_pyfunction!(univ_level_max, m)?)?;
    m.add_function(wrap_pyfunction!(univ_level_imax, m)?)?;

    Ok(())
}

// -------------------------------------------------------------------------
// Rust-native builder helpers and types
// -------------------------------------------------------------------------

/// Input type for universe-level builders in pure Rust.
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

/// Build a universe level from Rust input.
pub fn build_univ_level(level: UnivLevelInput) -> UnivLevel {
    match level {
        UnivLevelInput::Int(n) => {
            if n < 0 {
                panic!("Universe level must be non-negative, got {}", n);
            }
            let mut result = UnivLevel::Zero;
            for _ in 0..n {
                result = UnivLevel::Succ(Box::new(result));
            }
            result
        }
        UnivLevelInput::Param(name) => UnivLevel::Param(name),
        UnivLevelInput::Level(level) => level,
    }
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
