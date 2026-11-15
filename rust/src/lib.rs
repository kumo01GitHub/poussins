use pyo3::prelude::*;

pub mod ast;
pub mod builders;
pub mod environment;
pub mod state;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    ast::register(m)?;
    builders::register(m)?;

    Ok(())
}
