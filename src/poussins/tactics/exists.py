"""Existential introduction tactic."""
from ..ast import EApp, EConst, EMetaVar, Expr
from ..environment.library import LogicDeclaration
from ..errors import TacticError
from ..kernel import Goal, ProofManager, whnf
from .helpers import (
    build_app,
    const_from_decl,
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def use(manager: ProofManager, expr: Expr) -> None:
    """Refine the current goal of the form `Exists A P` by providing a witness."""
    current_goal = require_current_goal(manager, tactic_name="use")

    metavars = manager.current_state.metavars
    env = manager.env

    head = whnf(current_goal.statement, metavars, env)

    if not (
        isinstance(head, EApp)
        and isinstance(head.fn, EApp)
        and isinstance(head.fn.fn, EConst)
        and head.fn.fn.name == LogicDeclaration.EXISTS_DECLARATION.declaration.name
    ):
        raise TacticError("Goal is not an existential statement (Exists).")

    new_goal = Goal(
        statement=EApp(head.arg, expr),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    manager.refine_goal(
        build_app(
            const_from_decl(
                LogicDeclaration.EXISTS_INTRO_DECLARATION.declaration,
                manager
            ),
            head.fn.arg,
            head.arg,
            expr,
            EMetaVar(new_goal.id),
        ),
        [new_goal]
    )


# Alias for use tactic
exists = use
