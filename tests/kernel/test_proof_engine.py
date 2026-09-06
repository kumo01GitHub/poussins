"""Mathematical and state-transition tests for `poussins.kernel.proof_engine`."""
from __future__ import annotations

import pytest

from poussins.ast import (
    EApp,
    ELam,
    EMetaVar,
    ESort,
    EVar,
    Expr,
    UnivLevelSucc,
    UnivLevelZero,
)
from poussins.environment import Environment
from poussins.errors import KernelStateError, KernelTypeError, KernelValueError
from poussins.kernel.goal import Goal
from poussins.kernel.proof_engine import ProofEngine
from poussins.kernel.proof_state import MetaVar, ProofState


class TestCreateInitialState:
    """Initialization rule for the proof engine."""

    prop = ESort(UnivLevelZero())

    def test_creates_single_goal_with_root_metavar(self):
        """Initial state has one active goal and one unsolved root metavariable."""
        env = Environment()
        engine = ProofEngine()

        state = engine.create_initial_state(self.prop, env)

        assert len(state.goals) == 1
        goal = state.current_goal
        assert goal is not None
        assert goal.statement == self.prop
        assert goal.context == env.to_context()
        assert goal.local_hypothesis_names == frozenset()

        assert goal.id in state.metavars
        assert state.metavars[goal.id].statement == self.prop
        assert state.metavars[goal.id].is_assigned is False


class TestCloseGoal:
    """Goal-closing rule: assignment must typecheck and unify with the goal."""

    prop = ESort(UnivLevelZero())
    type0 = ESort(UnivLevelSucc(UnivLevelZero()))

    def test_closes_goal_when_assignment_has_goal_type(self):
        """A well-typed witness closes the current goal."""
        env = Environment()
        engine = ProofEngine()
        state = engine.create_initial_state(self.type0, env)

        next_state = engine.close_goal(state, self.prop, env)

        assert next_state.goals == ()
        root_id = state.current_goal.id if state.current_goal is not None else ""
        assert next_state.metavars[root_id].assignment == self.prop

    def test_fails_when_no_active_goal(self):
        """Closing without an active goal is a state error."""
        engine = ProofEngine()
        with pytest.raises(KernelStateError):
            engine.close_goal(ProofState(), self.prop, Environment())

    def test_fails_when_assignment_type_does_not_unify(self):
        """An ill-typed witness relative to the goal is rejected."""
        env = Environment()
        engine = ProofEngine()
        state = engine.create_initial_state(self.prop, env)
        with pytest.raises(KernelTypeError):
            engine.close_goal(state, self.prop, env)


class TestRefineGoal:
    """Refinement rule for decomposing a goal into subgoals."""

    prop = ESort(UnivLevelZero())

    def test_refinement_registers_subgoal_in_order(self):
        """Refinement accepts assignments whose active metavariables match subgoals."""
        env = Environment()
        engine = ProofEngine()
        state = engine.create_initial_state(self.prop, env)

        subgoal = Goal(
            statement=self.prop,
            context=env.to_context(),
            local_hypothesis_names=frozenset(),
        )
        assignment = EMetaVar(subgoal.id)

        next_state = engine.refine_goal(state, assignment, [subgoal], env)

        assert tuple(g.id for g in next_state.goals) == (subgoal.id,)
        assert next_state.metavars[subgoal.id].statement == self.prop
        root_id = state.current_goal.id if state.current_goal is not None else ""
        assert next_state.metavars[root_id].assignment == assignment

    def test_refinement_fails_when_no_active_goal(self):
        """Refinement without an active goal is a state error."""
        engine = ProofEngine()
        with pytest.raises(KernelStateError):
            engine.refine_goal(ProofState(), self.prop, [], Environment())

    def test_refinement_rejects_mismatched_subgoal_witnesses(self):
        """Refinement rejects subgoal lists that do not match assignment witnesses."""
        env = Environment()
        engine = ProofEngine()
        state = engine.create_initial_state(self.prop, env)

        sg1 = Goal(self.prop, env.to_context(), frozenset())
        sg2 = Goal(self.prop, env.to_context(), frozenset())
        assignment = EApp(EMetaVar(sg1.id), EMetaVar(sg2.id))

        with pytest.raises(KernelValueError):
            engine.refine_goal(state, assignment, [sg1], env)

    def test_refinement_rejects_already_registered_subgoal_id(self):
        """Refinement cannot register a subgoal metavariable twice."""
        env = Environment()
        engine = ProofEngine()
        state = engine.create_initial_state(self.prop, env)
        current_goal = state.current_goal
        assert current_goal is not None

        reused = Goal(self.prop, env.to_context(), frozenset())
        object.__setattr__(reused, "id", current_goal.id)
        assignment = EMetaVar(current_goal.id)

        with pytest.raises(KernelStateError):
            engine.refine_goal(state, assignment, [reused], env)


class TestChangeGoal:
    """Goal-conversion rule: replace by a definitionally equal statement."""

    prop = ESort(UnivLevelZero())

    def _state_with_statement(self, statement: EVar) -> tuple[ProofState, Environment]:
        env = Environment()
        context: dict[str, Expr] = {"x": self.prop, "z": self.prop}
        goal = Goal(
            statement=statement,
            context=context,
            local_hypothesis_names=frozenset(),
        )
        state = ProofState(
            goals=(goal,),
            metavars={goal.id: MetaVar(statement=statement)},
        )
        return state, env

    def test_changes_goal_for_definitionally_equal_statement(self):
        """Changing to a convertible statement preserves logical meaning."""
        engine = ProofEngine()
        state, env = self._state_with_statement(EVar("x"))
        goal_before = state.current_goal
        assert goal_before is not None
        new_statement = EApp(ELam("y", self.prop, EVar("y")), EVar("x"))

        next_state = engine.change_goal(state, new_statement, env)
        assert next_state.current_goal is not None
        assert next_state.current_goal.id == goal_before.id
        assert next_state.current_goal.statement == new_statement
        assert (
            next_state.metavars[next_state.current_goal.id].statement
            == new_statement
        )

    def test_change_goal_fails_when_no_active_goal(self):
        """Changing goal without an active goal is a state error."""
        engine = ProofEngine()
        with pytest.raises(KernelStateError):
            engine.change_goal(ProofState(), self.prop, Environment())

    def test_rejects_ill_typed_new_statement(self):
        """Changing goal fails when the replacement is not well-typed."""
        engine = ProofEngine()
        state, env = self._state_with_statement(EVar("x"))
        with pytest.raises(KernelValueError):
            engine.change_goal(state, EVar("unknown"), env)

    def test_rejects_non_definitionally_equal_statement(self):
        """Changing goal fails for non-convertible statements."""
        engine = ProofEngine()
        state, env = self._state_with_statement(EVar("x"))
        with pytest.raises(KernelValueError):
            engine.change_goal(state, EVar("z"), env)


class TestChangeHypothesis:
    """Hypothesis-conversion rule in local context."""

    prop = ESort(UnivLevelZero())
    type0 = ESort(UnivLevelSucc(UnivLevelZero()))

    def _state_with_local_hyp(self) -> tuple[ProofState, Environment]:
        env = Environment()
        context: dict[str, Expr] = {"h": self.prop}
        goal = Goal(
            statement=EVar("h"),
            context=context,
            local_hypothesis_names=frozenset({"h"}),
        )
        state = ProofState(
            goals=(goal,),
            metavars={goal.id: MetaVar(statement=EVar("h"))},
        )
        return state, env

    def test_changes_hypothesis_for_definitionally_equal_type(self):
        """Changing local type is allowed only up to definitional equality."""
        engine = ProofEngine()
        state, env = self._state_with_local_hyp()
        goal_before = state.current_goal
        assert goal_before is not None
        new_type = EApp(ELam("T", self.type0, EVar("T")), self.prop)

        next_state = engine.change_hypothesis(state, "h", new_type, env)
        assert next_state.current_goal is not None
        assert next_state.current_goal.id == goal_before.id
        assert next_state.current_goal.local_context["h"] == new_type

    def test_change_hypothesis_fails_when_no_active_goal(self):
        """Changing hypothesis without an active goal is a state error."""
        engine = ProofEngine()
        with pytest.raises(KernelStateError):
            engine.change_hypothesis(ProofState(), "h", self.prop, Environment())

    def test_rejects_unknown_hypothesis(self):
        """Changing an unknown local hypothesis fails."""
        engine = ProofEngine()
        state, env = self._state_with_local_hyp()
        with pytest.raises(KernelValueError):
            engine.change_hypothesis(state, "x", self.prop, env)

    def test_rejects_ill_typed_new_hypothesis_type(self):
        """Changing hypothesis fails when the replacement type is ill-typed."""
        engine = ProofEngine()
        state, env = self._state_with_local_hyp()
        with pytest.raises(KernelValueError):
            engine.change_hypothesis(state, "h", EVar("unknown"), env)

    def test_rejects_non_definitionally_equal_hypothesis_type(self):
        """Changing hypothesis fails when types are not definitionally equal."""
        engine = ProofEngine()
        state, env = self._state_with_local_hyp()
        with pytest.raises(KernelValueError):
            engine.change_hypothesis(state, "h", self.type0, env)
