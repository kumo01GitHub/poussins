"""Tactic for case-splitting on an inductive hypothesis."""
from __future__ import annotations

from collections.abc import Sequence

from ..ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
    UnivLevelParam,
    substitute_expr_var,
)
from ..environment import ConstructorDeclaration, InductiveDeclaration
from ..errors import TacticError
from ..kernel import Goal, ProofManager, whnf
from .helpers import (
    build_lambda_chain,
    const_head_name,
    fresh_binder_name,
    require_current_goal,
    requires_active_goal,
)


def _build_constructor_pattern(
    constructor: EConst,
    constructor_type: Expr,
    context: dict[str, Expr],
    used_names: set[str],
) -> tuple[Expr, list[tuple[str, Expr]]]:
    """Build a constructor application and the list of branch binders for one case."""
    pattern = constructor
    branch_binders: list[tuple[str, Expr]] = []
    current_context = dict(context)
    current_type = constructor_type

    while isinstance(current_type, EPi):
        var_name = fresh_binder_name(current_type.var, current_context, used_names)
        current_context[var_name] = current_type.domain
        branch_binders.append((var_name, current_type.domain))
        pattern = EApp(pattern, EVar(var_name))
        current_type = current_type.body

    return pattern, branch_binders


def _collect_pi_binders(expr: Expr) -> list[str]:
    """Collect the binder names from a Pi-chain expression."""
    binders: list[str] = []
    current = expr
    while isinstance(current, EPi):
        binders.append(current.var)
        current = current.body
    return binders


def _normalize_patterns(
    patterns: tuple[tuple[str, ...], ...] | None, constructor_names: Sequence[str]
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Normalize user-provided patterns into (constructor, binder_names) pairs."""
    if patterns is None:
        return tuple((name, ()) for name in constructor_names)

    normalized_patterns: list[tuple[str, tuple[str, ...]]] = []
    for pattern in patterns:
        if not pattern:
            raise TacticError("empty patterns are not supported.")
        normalized_patterns.append((pattern[0], tuple(pattern[1:])))
    return tuple(normalized_patterns)


def _infer_inductive_parameter_substitutions(
    target_expr: Expr, actual_expr: Expr
) -> dict[str, Expr]:
    """Infer substitutions for an inductive constructor's parameters."""
    substitutions: dict[str, Expr] = {}

    def visit(expr: Expr, value: Expr) -> None:
        if isinstance(expr, EVar):
            substitutions[expr.name] = value
            return

        if isinstance(expr, EApp) and isinstance(value, EApp):
            visit(expr.fn, value.fn)
            visit(expr.arg, value.arg)
            return

        if isinstance(expr, EConst) and isinstance(value, EConst):
            if expr.name != value.name or expr.levels != value.levels:
                raise TacticError("could not infer constructor argument types.")
            return

        if isinstance(expr, ESort) and isinstance(value, ESort):
            return

        if isinstance(expr, EMetaVar) and isinstance(value, EMetaVar):
            if expr.goal_id != value.goal_id:
                raise TacticError("could not infer constructor argument types.")
            return

        if isinstance(expr, EPi) and isinstance(value, EPi):
            visit(expr.domain, value.domain)
            visit(expr.body, value.body)
            return

        if type(expr) is type(value):
            return

        raise TacticError("could not infer constructor argument types.")

    visit(target_expr, actual_expr)
    return substitutions


def _specialize_with_parameter_substitutions(
    expr: Expr, substitutions: dict[str, Expr]
) -> Expr:
    """Specialize an expression by substituting inferred inductive parameters."""
    specialized_expr = expr
    for param_name, param_value in substitutions.items():
        specialized_expr = substitute_expr_var(
            specialized_expr, param_name, param_value
        )
    return specialized_expr


def _build_branch_local_context(
    current_goal: Goal,
    hypothesis_name: str,
    constructor_pattern: Expr,
    branch_binders: list[tuple[str, Expr]],
    branch_alias_spec: tuple[
        list[tuple[str, Expr]], tuple[str, ...], dict[str, Expr]
    ],
) -> dict[str, Expr]:
    """Build the local context for one constructor branch."""
    (
        constructor_arg_binders,
        names_for_branch,
        parameter_substitutions,
    ) = branch_alias_spec

    branch_local_context = {
        name: substitute_expr_var(type_expr, hypothesis_name, constructor_pattern)
        for name, type_expr in current_goal.local_context.items()
        if name != hypothesis_name
    }
    for var_name, var_type in branch_binders:
        branch_local_context[var_name] = var_type

    if len(names_for_branch) > len(constructor_arg_binders):
        raise TacticError("too many branch names for constructor pattern.")

    for branch_name, (_, binder_type) in zip(
        names_for_branch,
        constructor_arg_binders[-len(names_for_branch):],
        strict=False,
    ):
        branch_local_context[branch_name] = _specialize_with_parameter_substitutions(
            binder_type, parameter_substitutions
        )

    branch_local_context[hypothesis_name] = substitute_expr_var(
        current_goal.local_context[hypothesis_name],
        hypothesis_name,
        constructor_pattern,
    )
    return branch_local_context


@requires_active_goal
def cases(
    manager: ProofManager,
    hypothesis_name: str,
    patterns: tuple[tuple[str, ...], ...] | None = None,
) -> None:
    """Case-split on an inductive hypothesis."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    if not current_goal.has_local_hypothesis(hypothesis_name):
        raise TacticError(f"Unknown hypothesis '{hypothesis_name}'.")

    hypothesis_type = whnf(
        current_goal.local_context[hypothesis_name],
        state.metavars,
        manager.env
    )
    head_name = const_head_name(hypothesis_type)
    if head_name is None:
        raise TacticError(
            "Hypothesis type must be an inductive type, "
            + f"but found non-constant head: {hypothesis_type}"
        )

    inductive_decl = manager.env.get(head_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(f"'{head_name}' is not an inductive type.")
    if not inductive_decl.constructor_names:
        raise TacticError(f"Inductive type '{head_name}' has no constructors.")

    inductive_parameters = _collect_pi_binders(inductive_decl.type)
    normalized_patterns = _normalize_patterns(
        patterns, inductive_decl.constructor_names
    )

    subgoals: list[Goal] = []
    branch_terms: list[Expr] = []

    for constructor_name, names_for_branch in normalized_patterns:
        constructor_decl = manager.env.get(constructor_name)
        if not isinstance(constructor_decl, ConstructorDeclaration):
            raise TacticError(f"'{constructor_name}' is not a constructor declaration.")

        constructor = EConst(
            name=constructor_name,
            levels=tuple(
                UnivLevelParam(param) for param in constructor_decl.level_params
            )
        )
        constructor_pattern, branch_binders = _build_constructor_pattern(
            constructor=constructor,
            constructor_type=constructor_decl.type,
            context=current_goal.context,
            used_names=set(),
        )

        constructor_return_type = constructor_decl.type
        while isinstance(constructor_return_type, EPi):
            constructor_return_type = constructor_return_type.body

        parameter_substitutions = _infer_inductive_parameter_substitutions(
            target_expr=constructor_return_type,
            actual_expr=hypothesis_type,
        )
        constructor_arg_binders = branch_binders[len(inductive_parameters):]

        branch_goal_statement = substitute_expr_var(
            current_goal.statement,
            hypothesis_name,
            constructor_pattern,
        )
        branch_local_context = _build_branch_local_context(
            current_goal=current_goal,
            hypothesis_name=hypothesis_name,
            constructor_pattern=constructor_pattern,
            branch_binders=branch_binders,
            branch_alias_spec=(
                constructor_arg_binders,
                names_for_branch,
                parameter_substitutions,
            ),
        )

        branch_goal = Goal(
            statement=branch_goal_statement,
            context=current_goal.global_context | branch_local_context,
            local_hypothesis_names=frozenset(branch_local_context.keys()),
        )
        subgoals.append(branch_goal)
        branch_terms.append(
            build_lambda_chain(constructor_arg_binders, EMetaVar(branch_goal.id))
        )

    motive = ELam(
        "_case",
        hypothesis_type,
        substitute_expr_var(current_goal.statement, hypothesis_name, EVar("_case")),
    )
    assignment = EMatch(head_name, EVar(hypothesis_name), motive, tuple(branch_terms))

    manager.refine_goal(assignment, subgoals)
