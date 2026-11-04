pub mod expr;
pub mod univ_level;

use pyo3::prelude::*;

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    univ_level::register(m)?;
    expr::register(m)?;

    Ok(())
}
