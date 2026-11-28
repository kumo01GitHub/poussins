//! Pure state-transition engine for the poussins elaborator.
//!
//! Operates on immutable input `&Snapshot` values and produces validated next `Snapshot`s
//! (or `KernelError`), keeping transaction history (`Session`) and PyO3 state (`Manager`)
//! strictly decoupled.

use std::collections::{HashMap, HashSet};
use std::sync::Arc;

use crate::ast::expr::Expr;
use crate::ast::ops::{collect_fvar_names, collect_mvar_ids};
use crate::elaborator::calc::{instantiate_mvars_arc, whnf_arc};
use crate::elaborator::unification::unify_arc;
use crate::environment::environment::Environment;
use crate::error::KernelError;
use crate::kernel::inference::{infer_arc_with_mvar, InferScope};
use crate::state::goal::Goal;
use crate::state::snapshot::Snapshot;

/// Create the initial [`Snapshot`] for proving `statement` under `env`.
pub fn create_initial_snapshot(
    statement: Expr,
    env: &Environment,
) -> Result<Snapshot, KernelError> {
    let empty_snapshot = Snapshot::new(HashMap::new(), vec![]);
    if !collect_open_mvar_ids(&statement, &empty_snapshot)?.is_empty() {
        return Err(KernelError::InvalidValue {
            message: "Initial goal statement cannot contain metavariables.".to_string(),
            expr: Some(statement),
        });
    }

    ensure_is_type(&statement, &[], env, &empty_snapshot)?;

    let initial_goal = Goal::new(statement, vec![]);
    let root_id = initial_goal.id.clone();
    let mut goals = HashMap::new();
    goals.insert(root_id.clone(), initial_goal);
    Ok(Snapshot::new(goals, vec![root_id]))
}

/// Close the current active goal by assigning a complete proof term `assignment`.
pub fn close_goal(
    snapshot: &Snapshot,
    assignment: Expr,
    env: &Environment,
) -> Result<Snapshot, KernelError> {
    let current_goal = snapshot.current_goal().ok_or_else(|| KernelError::InvalidValue {
        message: "No active goal to close.".to_string(),
        expr: None,
    })?;

    let open_mvars = collect_open_mvar_ids(&assignment, snapshot)?;
    if !open_mvars.is_empty() {
        return Err(KernelError::InvalidValue {
            message: format!(
                "Cannot close goal with unresolved metavariables: {open_mvars:?}. Use refine_goal instead."
            ),
            expr: Some(assignment),
        });
    }

    ensure_in_goal_scope(&assignment, current_goal)?;

    let mut next = snapshot.clone();
    next.assign(&current_goal.id, assignment.clone());

    let inferred_ty = infer_in_goal(&assignment, &current_goal.local_context, env, &next)?;
    let target_ty = Arc::new(current_goal.statement.clone());

    if !unify_arc(&inferred_ty, &target_ty, env, &mut next)? {
        return Err(KernelError::TypeMismatch {
            expected: current_goal.statement.clone(),
            actual: (*inferred_ty).clone(),
            context_expr: Some(assignment),
        });
    }

    prune_closed_goals(&mut next);
    Ok(next)
}

/// Refine the current active goal with a partial term `assignment` and ordered `subgoals`.
pub fn refine_goal(
    snapshot: &Snapshot,
    assignment: Expr,
    subgoals: Vec<Goal>,
    env: &Environment,
) -> Result<Snapshot, KernelError> {
    let current_goal = snapshot.current_goal().ok_or_else(|| KernelError::InvalidValue {
        message: "No active goal to refine.".to_string(),
        expr: None,
    })?;

    // 1. Validate subgoal freshness and well-typedness before registering.
    let mut seen_subgoal_ids = HashSet::with_capacity(subgoals.len());
    for sg in &subgoals {
        if snapshot.goals.contains_key(&sg.id) {
            return Err(KernelError::InvalidValue {
                message: format!(
                    "Meta-variable ?{} is already registered in the proof state.",
                    sg.id
                ),
                expr: Some(sg.statement.clone()),
            });
        }
        if !seen_subgoal_ids.insert(sg.id.clone()) {
            return Err(KernelError::InvalidValue {
                message: format!("Duplicate subgoal ID '?{}' provided to refine_goal.", sg.id),
                expr: Some(sg.statement.clone()),
            });
        }
        ensure_is_type(&sg.statement, &sg.local_context, env, snapshot)?;
    }

    // 2. Verify 1-to-1 correspondence between open MVars in `assignment` and `subgoals`.
    let active_mvar_ids = collect_open_mvar_ids(&assignment, snapshot)?;
    let subgoal_ids: Vec<String> = subgoals.iter().map(|g| g.id.clone()).collect();
    if active_mvar_ids != subgoal_ids {
        return Err(KernelError::InvalidValue {
            message: format!(
                "Subgoal mismatch with assignment expressions.\n  Expected from assignment (in order): {active_mvar_ids:?}\n  Provided subgoals:                   {subgoal_ids:?}"
            ),
            expr: Some(assignment),
        });
    }

    // 3. Verify free-variable scope in `current_goal`.
    ensure_in_goal_scope(&assignment, current_goal)?;

    // 4. Register subgoals and assign `current_goal` in a candidate snapshot.
    let mut next = snapshot.clone();
    for sg in &subgoals {
        next.goals.insert(sg.id.clone(), sg.clone());
    }
    next.assign(&current_goal.id, assignment.clone());

    // 5. Typecheck & unify `infer(assignment)` with `current_goal.statement`.
    let inferred_ty = infer_in_goal(&assignment, &current_goal.local_context, env, &next)?;
    let target_ty = Arc::new(current_goal.statement.clone());

    if !unify_arc(&inferred_ty, &target_ty, env, &mut next)? {
        return Err(KernelError::TypeMismatch {
            expected: current_goal.statement.clone(),
            actual: (*inferred_ty).clone(),
            context_expr: Some(assignment),
        });
    }

    // 6. Prepend newly created open subgoals ahead of remaining active goals,
    //    filtering out any goal already solved during unification.
    let existing_queue = next.goal_queue.clone();
    let mut new_queue = Vec::with_capacity(subgoals.len() + existing_queue.len());
    for sg in subgoals {
        if !is_goal_assigned(&next, &sg.id) {
            new_queue.push(sg.id);
        }
    }
    for id in existing_queue.into_iter().skip(1) {
        if !is_goal_assigned(&next, &id) {
            new_queue.push(id);
        }
    }
    next.goal_queue = new_queue;

    Ok(next)
}

/// Replace the current goal statement and/or local hypothesis types with definitionally
/// equal expressions in a single atomic transition.
pub fn change(
    snapshot: &Snapshot,
    new_statement: Option<Expr>,
    hypothesis_updates: &[(String, Expr)],
    env: &Environment,
) -> Result<Snapshot, KernelError> {
    let current_goal = snapshot.current_goal().ok_or_else(|| KernelError::InvalidValue {
        message: "No active goal to change.".to_string(),
        expr: None,
    })?;

    if new_statement.is_none() && hypothesis_updates.is_empty() {
        return Ok(snapshot.clone());
    }

    let mut next = snapshot.clone();
    let mut updated_local_context = current_goal.local_context.clone();
    let mut seen_hyp_names = HashSet::with_capacity(hypothesis_updates.len());

    // 1. Validate and apply each hypothesis type replacement.
    for (hyp_name, new_ty) in hypothesis_updates {
        if !seen_hyp_names.insert(hyp_name.as_str()) {
            return Err(KernelError::InvalidValue {
                message: format!("Duplicate hypothesis '{hyp_name}' in change updates."),
                expr: Some(new_ty.clone()),
            });
        }

        let hyp_pos = updated_local_context
            .iter()
            .rposition(|(name, _)| name == hyp_name)
            .ok_or_else(|| KernelError::InvalidValue {
                message: format!("change failed: Unknown hypothesis '{hyp_name}'."),
                expr: Some(new_ty.clone()),
            })?;

        let prefix_ctx = &updated_local_context[..hyp_pos];
        ensure_is_type(new_ty, prefix_ctx, env, &next)?;

        let old_ty_arc = Arc::new(updated_local_context[hyp_pos].1.clone());
        let new_ty_arc = Arc::new(new_ty.clone());
        if !unify_arc(&new_ty_arc, &old_ty_arc, env, &mut next)? {
            return Err(KernelError::TypeMismatch {
                expected: (*old_ty_arc).clone(),
                actual: new_ty.clone(),
                context_expr: Some(new_ty.clone()),
            });
        }

        updated_local_context[hyp_pos].1 = new_ty.clone();
    }

    // 2. Validate and apply the target statement replacement, if provided.
    let updated_statement = if let Some(stmt) = new_statement {
        ensure_is_type(&stmt, &updated_local_context, env, &next)?;

        let old_stmt_arc = Arc::new(current_goal.statement.clone());
        let new_stmt_arc = Arc::new(stmt.clone());
        if !unify_arc(&new_stmt_arc, &old_stmt_arc, env, &mut next)? {
            return Err(KernelError::TypeMismatch {
                expected: current_goal.statement.clone(),
                actual: stmt,
                context_expr: None,
            });
        }
        stmt
    } else {
        current_goal.statement.clone()
    };

    // 3. Commit updated goal record and prune any goals resolved by unification.
    let goal_id = current_goal.id.clone();
    if let Some(goal_entry) = next.goals.get_mut(&goal_id) {
        goal_entry.local_context = updated_local_context;
        goal_entry.statement = updated_statement;
    }
    prune_closed_goals(&mut next);

    Ok(next)
}

// ---------------------------------------------------------------------------
// Internal Helpers
// ---------------------------------------------------------------------------

#[inline]
fn is_goal_assigned(snapshot: &Snapshot, goal_id: &str) -> bool {
    snapshot
        .goals
        .get(goal_id)
        .is_some_and(|g| g.assignment.is_some())
}

#[inline]
fn prune_closed_goals(snapshot: &mut Snapshot) {
    let assigned_ids: HashSet<String> = snapshot
        .goals
        .iter()
        .filter_map(|(id, g)| g.assignment.as_ref().map(|_| id.clone()))
        .collect();
    snapshot.goal_queue.retain(|id| !assigned_ids.contains(id));
}

fn collect_open_mvar_ids(expr: &Expr, snapshot: &Snapshot) -> Result<Vec<String>, KernelError> {
    let instantiated = instantiate_mvars_arc(&Arc::new(expr.clone()), snapshot)?;
    Ok(collect_mvar_ids(&instantiated))
}

fn ensure_in_goal_scope(expr: &Expr, goal: &Goal) -> Result<(), KernelError> {
    for name in collect_fvar_names(expr) {
        if !goal.has_local_hypothesis(&name) {
            return Err(KernelError::UnknownFVar { name });
        }
    }
    Ok(())
}

fn infer_in_goal(
    expr: &Expr,
    local_context: &[(String, Expr)],
    env: &Environment,
    snapshot: &Snapshot,
) -> Result<Arc<Expr>, KernelError> {
    let mut scope = InferScope::new(local_context);
    infer_arc_with_mvar(&Arc::new(expr.clone()), env, &mut scope, &mut |mvar_id| {
        let goal = snapshot.goals.get(mvar_id).ok_or_else(|| KernelError::InvalidValue {
            message: format!("Unknown metavariable '?{mvar_id}'"),
            expr: Some(expr.clone()),
        })?;
        instantiate_mvars_arc(&Arc::new(goal.statement.clone()), snapshot)
    })
}

fn ensure_is_type(
    ty: &Expr,
    local_context: &[(String, Expr)],
    env: &Environment,
    snapshot: &Snapshot,
) -> Result<(), KernelError> {
    let inferred_sort = infer_in_goal(ty, local_context, env, snapshot)?;
    let reduced = whnf_arc(&inferred_sort, env, snapshot)?;
    if !matches!(*reduced, Expr::Sort(_)) {
        return Err(KernelError::NotASort {
            expr: ty.clone(),
            inferred_type: (*reduced).clone(),
        });
    }
    Ok(())
}
