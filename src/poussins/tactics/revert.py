from __future__ import annotations

from ..ast import EApp, EMetaVar, EPi, EVar, collect_free_vars
from ..errors import TacticError
from ..kernel import Goal, ProofManager


def revert(manager: ProofManager, hyp_names: str | list[str]) -> None:
    """Revert one or more hypotheses from the local context back into the goal."""
    targets = [hyp_names] if isinstance(hyp_names, str) else hyp_names

    if not targets:
        raise TacticError("No hypothesis names provided.")

    for hyp_name in targets:
        current_goal = manager.current_state.current_goal
        if current_goal is None:
            raise TacticError("No active goal.")

        if hyp_name not in current_goal.local_context:
            raise TacticError(f"Hypothesis '{hyp_name}' not found in local context.")

        hyp_type = current_goal.context[hyp_name]

        for name, expr in current_goal.local_context.items():
            if name != hyp_name and hyp_name in collect_free_vars(expr):
                raise TacticError(
                    f"Cannot revert '{hyp_name}' because '{name}' depends on it."
                )

        new_goal = Goal(
            statement=EPi(var=hyp_name, domain=hyp_type, body=current_goal.statement),
            context={
                name: expr
                for name, expr in current_goal.context.items()
                if name != hyp_name
            },
            local_hypothesis_names=(
                current_goal.local_hypothesis_names - {hyp_name}
                if current_goal.local_hypothesis_names is not None
                else None
            ),
        )

        manager.refine_goal(
            EApp(fn=EMetaVar(new_goal.id), arg=EVar(hyp_name)),
            [new_goal]
        )
