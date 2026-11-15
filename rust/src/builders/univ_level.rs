/// Builder functions for constructing universe levels.
///
/// This module provides ergonomic universe-level constructors, matching the
/// Python-side builder style while keeping universe logic separate from
/// expression builders.

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyTuple};

use crate::ast::univ_level::{to_pyresult, UnivLevel};

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
    to_pyresult(py, lvl)
}

/// Build multiple universe levels from a sequence of level inputs.
#[pyfunction]
#[pyo3(signature = (levels))]
pub fn univ_levels(py: Python<'_>, levels: &Bound<'_, PyAny>) -> PyResult<Py<PyTuple>> {
    let mut py_levels = Vec::new();
    for item in levels.try_iter()? {
        let item = item?;
        let lvl = extract_univ_level(&item)?;
        let py_obj = to_pyresult(py, lvl)?;
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
    to_pyresult(py, result)
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
    to_pyresult(py, res)
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_univ_level_zero() {
        let level = build_univ_level(0i64.into());
        assert!(matches!(level, UnivLevel::Zero));
    }

    #[test]
    fn test_univ_level_succ() {
        let level = build_univ_level(2i64.into());
        match level {
            UnivLevel::Succ(pred) => match *pred {
                UnivLevel::Succ(inner_pred) => {
                    assert!(matches!(*inner_pred, UnivLevel::Zero));
                }
                _ => panic!("Expected nested Succ"),
            },
            _ => panic!("Expected Succ"),
        }
    }

    #[test]
    fn test_univ_level_param() {
        let level = build_univ_level("u".into());
        match level {
            UnivLevel::Param(name) => assert_eq!(name, "u"),
            _ => panic!("Expected Param"),
        }
    }

    #[test]
    fn test_univ_levels() {
        let levels = build_univ_levels(vec![
            UnivLevelInput::Int(0),
            UnivLevelInput::Param("u".to_string()),
            UnivLevelInput::Level(UnivLevel::Zero),
        ]);
        assert_eq!(levels.len(), 3);
        assert!(matches!(levels[0], UnivLevel::Zero));
        assert!(matches!(levels[1], UnivLevel::Param(ref name) if name == "u"));
        assert!(matches!(levels[2], UnivLevel::Zero));
    }

    #[test]
    fn test_univ_level_max_single_fallback() {
        let level = build_univ_level_max(vec![UnivLevelInput::Param("u".to_string())]);
        assert!(matches!(level, UnivLevel::Param(ref name) if name == "u"));
    }

    #[test]
    fn test_univ_level_max_multiple() {
        let level = build_univ_level_max(vec![
            UnivLevelInput::Param("u".to_string()),
            UnivLevelInput::Param("v".to_string()),
            UnivLevelInput::Int(0),
        ]);
        match level {
            UnivLevel::Max(left, right) => {
                assert!(matches!(*right, UnivLevel::Zero));
                assert!(matches!(*left, UnivLevel::Max(_, _)));
            }
            _ => panic!("Expected Max"),
        }
    }

    #[test]
    fn test_univ_level_imax() {
        let level = build_univ_level_imax("u".into(), "v".into());
        match level {
            UnivLevel::IMax(left, right) => {
                assert!(matches!(*left, UnivLevel::Param(ref name) if name == "u"));
                assert!(matches!(*right, UnivLevel::Param(ref name) if name == "v"));
            }
            _ => panic!("Expected IMax"),
        }
    }

    #[test]
    #[should_panic(expected = "Universe level must be non-negative")]
    fn test_univ_level_negative() {
        build_univ_level((-1i64).into());
    }

    #[test]
    #[should_panic(expected = "univ_level_max requires at least one level")]
    fn test_univ_level_max_empty_panics() {
        let _ = build_univ_level_max(Vec::<UnivLevelInput>::new());
    }
}
