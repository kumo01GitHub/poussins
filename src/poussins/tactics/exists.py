"""Existential introduction tactic."""
from ..ast import EApp, EConst, EMetaVar, Expr, app
from ..environment import const
from ..environment.library import EXISTS_IND_SPEC
from ..errors import TacticError
from ..kernel import Goal, ProofManager, whnf
from .helpers import (
    require_current_goal,
    requires_active_goal,
)


@requires_active_goal
def use(manager: ProofManager, term: Expr) -> None:
    """Refine the current goal of the form `Exists A P` by providing a witness."""
    current_goal = require_current_goal(manager, tactic_name="use")

    metavars = manager.current_state.metavars
    env = manager.env

    head = whnf(current_goal.statement, metavars, env)

    if not (
        isinstance(head, EApp)
        and isinstance(head.fn, EApp)
        and isinstance(head.fn.fn, EConst)
        and head.fn.fn.name == EXISTS_IND_SPEC.name
    ):
        raise TacticError("Goal is not an existential statement (Exists).")

    new_goal = Goal(
        statement=EApp(head.arg, term),
        context=current_goal.context,
        local_hypothesis_names=current_goal.local_hypothesis_names,
    )

    manager.refine_goal(
        app(
            const(
                env=manager.env,
                name=EXISTS_IND_SPEC.constructors[0][0],
            ),
            head.fn.arg,
            head.arg,
            term,
            EMetaVar(new_goal.id),
        ),
        [new_goal]
    )


# Alias for use tactic
exists = use
