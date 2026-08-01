from poussins.ast import EConst
from poussins.kernel.goal import Goal
from poussins.kernel.proof_state import MetaVar, ProofState


def test_goal_equality_uses_identity_id() -> None:
    goal1 = Goal(statement=EConst("True", ()), context={})
    goal2 = Goal(statement=EConst("True", ()), context={})

    assert goal1 != goal2


def test_metavar_is_assigned_property() -> None:
    unassigned = MetaVar(statement=EConst("True", ()))
    assigned = MetaVar(statement=EConst("True", ()), assignment=EConst("True.intro", ()))

    assert not unassigned.is_assigned
    assert assigned.is_assigned


def test_proof_state_current_goal_returns_first_goal() -> None:
    goal1 = Goal(statement=EConst("True", ()), context={})
    goal2 = Goal(statement=EConst("False", ()), context={})

    state = ProofState(
        goals=(goal1, goal2),
        metavars={goal1.id: MetaVar(statement=goal1.statement), goal2.id: MetaVar(statement=goal2.statement)},
    )

    assert state.current_goal == goal1


def test_proof_state_current_goal_is_none_when_empty() -> None:
    state = ProofState(goals=(), metavars={})
    assert state.current_goal is None
