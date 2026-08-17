"""
Tactic for case-splitting on an inductive hypothesis.
"""
from __future__ import annotations

from ..ast import (
    EApp,
    EConst,
    ELam,
    EMetaVar,
    EMatch,
    EPi,
    Expr,
    ESort,
    EVar,
    substitute_expr_var,
)
from ..environment import ConstructorDeclaration, InductiveDeclaration
from ..errors import TacticError
from ..kernel import Goal, ProofManager, whnf


def _fresh_name(base: str, context: dict[str, Expr], used_names: set[str]) -> str:
    """
    Produce a fresh binder name that does not collide with the current context.
    """
    candidate = base
    counter = 0
    while candidate in context or candidate in used_names:
        counter += 1
        candidate = f"{base}{counter}"
    return candidate


def _build_constructor_pattern(
    constructor: EConst,
    constructor_type: Expr,
    context: dict[str, Expr],
    used_names: set[str],
) -> tuple[Expr, list[tuple[str, Expr]]]:
    """
    Build a constructor application and the list of branch binders for one case.
    """
    pattern = constructor
    branch_binders: list[tuple[str, Expr]] = []
    current_context = dict(context)
    current_type = constructor_type

    while isinstance(current_type, EPi):
        var_name = _fresh_name(current_type.var, current_context, used_names)
        current_context[var_name] = current_type.domain
        branch_binders.append((var_name, current_type.domain))
        pattern = EApp(pattern, EVar(var_name))
        current_type = current_type.body

    return pattern, branch_binders


def _build_branch_expr(
    branch_binders: list[tuple[str, Expr]],
    subgoal_id: str,
) -> Expr:
    """
    Build a lambda expression for a branch body that returns the subgoal metavariable.
    """
    expr: Expr = EMetaVar(subgoal_id)
    for var_name, domain in reversed(branch_binders):
        expr = ELam(var_name, domain, expr)
    return expr


def _collect_pi_binders(expr: Expr) -> list[str]:
    """
    Collect the binder names from a Pi-chain expression.
    """
    binders: list[str] = []
    current = expr
    while isinstance(current, EPi):
        binders.append(current.var)
        current = current.body
    return binders


def _infer_inductive_parameter_substitutions(target_expr: Expr, actual_expr: Expr) -> dict[str, Expr]:
    """
    Infer substitutions for an inductive constructor's parameters by matching its return type
    against the scrutinee's concrete type.
    """
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
                raise TacticError("cases failed: could not infer constructor argument types.")
            return

        if isinstance(expr, ESort) and isinstance(value, ESort):
            return

        if isinstance(expr, EMetaVar) and isinstance(value, EMetaVar):
            if expr.goal_id != value.goal_id:
                raise TacticError("cases failed: could not infer constructor argument types.")
            return

        if isinstance(expr, EPi) and isinstance(value, EPi):
            visit(expr.domain, value.domain)
            visit(expr.body, value.body)
            return

        if type(expr) is type(value):
            return

        raise TacticError("cases failed: could not infer constructor argument types.")

    visit(target_expr, actual_expr)
    return substitutions


def cases(
    manager: ProofManager,
    hypothesis_name: str,
    patterns: tuple[tuple[str, ...], ...] | None = None,
) -> None:
    """
    Case-split on an inductive hypothesis and create one subgoal per selected constructor pattern.
    """
    if manager.is_closed:
        raise TacticError("cases failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    if current_goal is None:
        raise TacticError("cases failed: No active goals remain.")

    if not current_goal.has_local_hypothesis(hypothesis_name):
        raise TacticError(f"cases failed: Unknown hypothesis '{hypothesis_name}'.")

    hypothesis_type = whnf(current_goal.local_context[hypothesis_name], state.metavars, manager.engine.env)
    head_expr = hypothesis_type
    while isinstance(head_expr, EApp):
        head_expr = head_expr.fn

    head_name = getattr(head_expr, "name", None)
    if not head_name:
        raise TacticError(f"cases failed: Hypothesis type head has no name. Found: {hypothesis_type}")

    env = manager.env
    inductive_decl = env.get(head_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(f"cases failed: '{head_name}' is not an inductive type.")
    if not inductive_decl.constructor_names:
        raise TacticError(f"cases failed: Inductive type '{head_name}' has no constructors.")

    inductive_parameters = _collect_pi_binders(inductive_decl.type)

    if patterns is None:
        normalized_patterns = tuple((name, ()) for name in inductive_decl.constructor_names)
    else:
        normalized_patterns = []
        for pattern in patterns:
            if not pattern:
                raise TacticError("cases failed: empty patterns are not supported.")
            constructor_name = pattern[0]
            names_for_branch = tuple(pattern[1:])
            normalized_patterns.append((constructor_name, names_for_branch))

    subgoals: list[Goal] = []
    branch_terms: list[Expr] = []

    for constructor_name, names_for_branch in normalized_patterns:
        constructor_decl = env.get(constructor_name)
        if not isinstance(constructor_decl, ConstructorDeclaration):
            raise TacticError(f"cases failed: '{constructor_name}' is not a constructor declaration.")

        constructor = EConst(name=constructor_name, levels=constructor_decl.level_params)
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
        branch_local_context = {
            name: substitute_expr_var(type_expr, hypothesis_name, constructor_pattern)
            for name, type_expr in current_goal.local_context.items()
            if name != hypothesis_name
        }
        for var_name, var_type in branch_binders:
            branch_local_context[var_name] = var_type

        if len(names_for_branch) > len(constructor_arg_binders):
            raise TacticError("cases failed: too many branch names for constructor pattern.")
        for branch_name, (_, binder_type) in zip(names_for_branch, constructor_arg_binders[-len(names_for_branch):]):
            specialized_type = binder_type
            for param_name, param_value in parameter_substitutions.items():
                specialized_type = substitute_expr_var(specialized_type, param_name, param_value)
            branch_local_context[branch_name] = specialized_type

        branch_local_context[hypothesis_name] = substitute_expr_var(
            current_goal.local_context[hypothesis_name],
            hypothesis_name,
            constructor_pattern,
        )

        branch_goal = Goal(
            statement=branch_goal_statement,
            context=current_goal.global_context | branch_local_context,
            local_hypothesis_names=frozenset(branch_local_context.keys()),
        )
        subgoals.append(branch_goal)
        branch_terms.append(_build_branch_expr(constructor_arg_binders, branch_goal.id))

    motive = ELam(
        "_case",
        hypothesis_type,
        substitute_expr_var(current_goal.statement, hypothesis_name, EVar("_case")),
    )
    assignment = EMatch(head_name, EVar(hypothesis_name), motive, tuple(branch_terms))

    manager.refine_goal(assignment, subgoals)
