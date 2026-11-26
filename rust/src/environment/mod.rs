pub mod declaration;
pub mod environment;

use pyo3::prelude::*;

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    declaration::register(m)?;
    environment::register(m)?;
    Ok(())
}
