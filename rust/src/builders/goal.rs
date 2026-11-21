use pyo3::prelude::*;

use crate::ast::expr::Expr;
use crate::builders::expr::ExprInput;
use crate::state::goal::Goal;

/// Create a new proof subgoal (`Goal`) paired with its corresponding metavariable (`EMVar`).
///
/// The generated `Goal`'s unique UUID (or explicit `id`) is assigned to the returned `EMVar`.
#[pyfunction]
#[pyo3(signature = (statement, local_context = None, id = None))]
pub fn subgoal(
    statement: ExprInput,
    local_context: Option<Vec<(String, ExprInput)>>,
    id: Option<String>,
) -> (Goal, Expr) {
    let ctx: Vec<(String, Expr)> = local_context
        .unwrap_or_default()
        .into_iter()
        .map(|(name, ty)| (name, ty.0))
        .collect();

    let goal = match id {
        Some(explicit_id) => Goal::with_id(explicit_id, statement.0, ctx),
        None => Goal::new(statement.0, ctx),
    };
    let mvar = Expr::MVar(goal.id.clone());

    (goal, mvar)
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(subgoal, m)?)?;
    Ok(())
}
