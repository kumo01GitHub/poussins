"""Tactic for performing structural induction over an inductive hypothesis."""
from __future__ import annotations

from ..ast import (
    EApp,
    EConst,
    EFVar,
    EMetaVar,
    EPi,
    Expr,
    app,
    decompose_app,
    instantiate_binder,
    lam,
    substitute_var,
    univ_levels,
)
from ..environment import (
    ConstructorDeclaration,
    InductiveDeclaration,
    RecursorDeclaration,
)
from ..errors import TacticError
from ..kernel import Goal, ProofManager, whnf
from .helpers import (
    const_head_name,
    fresh_binder_name,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def induction(manager: ProofManager, hyp_name: str) -> None:  # noqa: PLR0915
    """Perform structural induction on an inductive hypothesis in the current goal.

    The tactic creates one subgoal per constructor of the inductive type.
    For each branch, the target is rewritten with the constructor application,
    and any constructor arguments whose types are the same inductive type receive
    an induction hypothesis of the form ``ih : P prev``.
    """
    state = manager.current_state
    current_goal = require_current_goal(manager)

    if not current_goal.has_local_hypothesis(hyp_name):
        raise TacticError(f"Unknown hypothesis '{hyp_name}'.")

    hypothesis_type = whnf(
        current_goal.local_context[hyp_name],
        state.metavars,
        manager.env
    )
    head_name = const_head_name(hypothesis_type)
    if head_name is None:
        raise TacticError(
            "Induction hypothesis type must be an inductive type, "
            + f"found non-constant head: {hypothesis_type}"
        )

    inductive_decl = manager.env.get(head_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(f"'{head_name}' is not an inductive type.")
    if not inductive_decl.constructor_names:
        raise TacticError(f"Inductive type '{head_name}' has no constructors.")

    constructor_names = inductive_decl.constructor_names
    _, hypothesis_args = decompose_app(hypothesis_type)
    recursor_decl = manager.env.get(inductive_decl.recursor_names[0])
    if not isinstance(recursor_decl, RecursorDeclaration):
        raise TacticError(f"Missing recursor declaration for '{head_name}'.")
    inductive_param_count = recursor_decl.num_params
    inductive_index_count = recursor_decl.num_indices
    subgoals: list[Goal] = []
    branch_terms: list[Expr] = []

    for constructor_name in constructor_names:
        constructor_decl = manager.env.get(constructor_name)
        if not isinstance(constructor_decl, ConstructorDeclaration):
            raise TacticError(f"'{constructor_name}' is not a constructor declaration.")

        constructor = EConst(
            name=constructor_name,
            levels=univ_levels(constructor_decl.level_params)
        )
        constructor_type = constructor_decl.type

        branch_binders: list[tuple[str, Expr]] = []
        branch_expr: Expr = constructor
        current_type = constructor_type
        while isinstance(current_type, EPi):
            var_name = fresh_binder_name(
                current_type.var,
                current_goal.context, used_names=set()
            )
            branch_binders.append((var_name, current_type.domain))
            branch_expr = EApp(branch_expr, EFVar(var_name))
            current_type = instantiate_binder(
                current_type.body, EFVar(var_name)
            )

        parameter_substitutions: dict[str, Expr] = {}
        for idx in range(
            min(inductive_param_count, len(hypothesis_args), len(branch_binders))
        ):
            p_var_name = branch_binders[idx][0]
            parameter_substitutions[p_var_name] = hypothesis_args[idx]

        constructor_arg_binders = branch_binders[inductive_param_count:]

        for p_name, p_value in parameter_substitutions.items():
            branch_expr = substitute_var(branch_expr, p_name, p_value)

        branch_statement = substitute_var(
            current_goal.statement,
            hyp_name,
            branch_expr
        )
        branch_local_context = {
            name: substitute_var(type_expr, hyp_name, branch_expr)
            for name, type_expr in current_goal.local_context.items()
            if name != hyp_name
        }
        branch_local_context[hyp_name] = branch_expr

        specialized_constructor_arg_binders = [
            (
                var_name,
                _specialize_with_parameter_substitutions(
                    var_type,
                    parameter_substitutions
                ),
            )
            for var_name, var_type in constructor_arg_binders
        ]

        for var_name, var_type in specialized_constructor_arg_binders:
            branch_local_context[var_name] = var_type

        induction_hypotheses: list[tuple[str, Expr]] = []
        for var_name, var_type in specialized_constructor_arg_binders:
            if const_head_name(var_type) == head_name:
                ih_name = fresh_binder_name(
                    "ih",
                    current_goal.global_context | branch_local_context,
                    used_names=set()
                )
                ih_expr = substitute_var(
                    current_goal.statement,
                    hyp_name,
                    EFVar(var_name)
                )
                branch_local_context[ih_name] = ih_expr
                induction_hypotheses.append((ih_name, EFVar(var_name)))

        subgoal = Goal(
            statement=branch_statement,
            context=current_goal.global_context | branch_local_context,
            local_hypothesis_names=frozenset(branch_local_context.keys()),
        )
        subgoals.append(subgoal)

        branch_terms.append(
            lam(specialized_constructor_arg_binders, EMetaVar(subgoal.id))
        )

    manager.refine_goal(
        app(
            EConst(f"{head_name}.casesOn", ()),
            *hypothesis_args[:inductive_param_count],
            *hypothesis_args[
                inductive_param_count:inductive_param_count
                + inductive_index_count
            ],
            EFVar(hyp_name),
            lam(
                (("_induction", hypothesis_type),),
                substitute_var(
                    current_goal.statement,
                    hyp_name,
                    EFVar("_induction")
                ),
            ),
            *branch_terms,
        ),
        subgoals
    )


def _specialize_with_parameter_substitutions(
    expr: Expr,
    substitutions: dict[str, Expr],
) -> Expr:
    """Specialize an expression by substituting inferred inductive parameters."""
    specialized_expr = expr
    for param_name, param_value in substitutions.items():
        specialized_expr = substitute_var(specialized_expr, param_name, param_value)
    return specialized_expr
