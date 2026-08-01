from poussins.ast import EConst
from poussins.kernel.goal import Goal


def test_goal_equality_uses_identity_id() -> None:
    goal1 = Goal(statement=EConst("True", ()), context={})
    goal2 = Goal(statement=EConst("True", ()), context={})

    assert goal1 != goal2


def test_goal_equality_returns_false_for_non_goal() -> None:
    goal = Goal(statement=EConst("True", ()), context={})

    assert goal != object()
