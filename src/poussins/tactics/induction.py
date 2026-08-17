"""
Tactic for performing structural induction over an inductive hypothesis.
"""
from __future__ import annotations

from ..ast import EApp, EConst, ELam, EMatch, EMetaVar, EPi, EVar, Expr, substitute_expr_var
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


def induction(manager: ProofManager, hypothesis_name: str) -> None:
    """
    Perform structural induction on an inductive hypothesis in the current goal.

    The tactic creates one subgoal per constructor of the inductive type.
    For each branch, the target is rewritten with the constructor application,
    and any constructor arguments whose types are the same inductive type receive
    an induction hypothesis of the form ``ih : P prev``.
    """
    if manager.is_closed:
        raise TacticError("induction failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    if current_goal is None:
        raise TacticError("induction failed: No active goals remain.")

    if not current_goal.has_local_hypothesis(hypothesis_name):
        raise TacticError(f"induction failed: Unknown hypothesis '{hypothesis_name}'.")

    hypothesis_type = whnf(current_goal.local_context[hypothesis_name], state.metavars, manager.env)
    head_expr = hypothesis_type
    while isinstance(head_expr, EApp):
        head_expr = head_expr.fn

    head_name = getattr(head_expr, "name", None)
    if not head_name:
        raise TacticError(f"induction failed: '{hypothesis_name}' has no inductive head. Found type '{hypothesis_type}'.")

    env = manager.env
    inductive_decl = env.get(head_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise TacticError(f"induction failed: '{head_name}' is not an inductive type.")
    if not inductive_decl.constructor_names:
        raise TacticError(f"induction failed: Inductive type '{head_name}' has no constructors.")

    constructor_names = inductive_decl.constructor_names
    subgoals: list[Goal] = []
    branch_terms: list[Expr] = []

    for constructor_name in constructor_names:
        constructor_decl = env.get(constructor_name)
        if not isinstance(constructor_decl, ConstructorDeclaration):
            raise TacticError(f"induction failed: '{constructor_name}' is not a constructor declaration.")

        constructor = EConst(name=constructor_name, levels=constructor_decl.level_params)
        constructor_type = constructor_decl.type

        branch_binders: list[tuple[str, Expr]] = []
        branch_expr: Expr = constructor
        current_type = constructor_type
        while isinstance(current_type, EPi):
            var_name = _fresh_name(current_type.var, current_goal.context, used_names=set())
            branch_binders.append((var_name, current_type.domain))
            branch_expr = EApp(branch_expr, EVar(var_name))
            current_type = current_type.body

        branch_statement = substitute_expr_var(current_goal.statement, hypothesis_name, branch_expr)
        branch_local_context = {
            name: substitute_expr_var(type_expr, hypothesis_name, branch_expr)
            for name, type_expr in current_goal.local_context.items()
            if name != hypothesis_name
        }
        branch_local_context[hypothesis_name] = branch_expr

        for var_name, var_type in branch_binders:
            branch_local_context[var_name] = var_type

        induction_hypotheses: list[tuple[str, Expr]] = []
        for var_name, var_type in branch_binders:
            if isinstance(var_type, EConst) and var_type.name == head_name:
                ih_name = _fresh_name("ih", current_goal.global_context | branch_local_context, used_names=set())
                ih_expr = substitute_expr_var(current_goal.statement, hypothesis_name, EVar(var_name))
                branch_local_context[ih_name] = ih_expr
                induction_hypotheses.append((ih_name, EVar(var_name)))

        subgoal = Goal(
            statement=branch_statement,
            context=current_goal.global_context | branch_local_context,
            local_hypothesis_names=frozenset(branch_local_context.keys()),
        )
        subgoals.append(subgoal)

        branch_term = EMetaVar(subgoal.id)
        for var_name, _ in reversed(branch_binders):
            branch_term = ELam(var_name, branch_local_context[var_name], branch_term)
        branch_terms.append(branch_term)

    motive = ELam(
        "_induction",
        hypothesis_type,
        substitute_expr_var(current_goal.statement, hypothesis_name, EVar("_induction")),
    )
    assignment = EMatch(head_name, EVar(hypothesis_name), motive, tuple(branch_terms))
    manager.refine_goal(assignment, subgoals)
