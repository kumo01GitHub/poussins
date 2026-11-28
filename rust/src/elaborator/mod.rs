pub mod calc;
pub mod engine;
pub mod manager;
pub mod unification;

use pyo3::prelude::*;

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    manager::register(m)?;

    Ok(())
}
