import pytest

from poussins import (
    Environment,
    EEq,
    EExists,
    EForall,
    EImp,
    ETop,
    FunctionSymbol,
    PForallE,
    PRefl,
    PVar,
    PredicateSymbol,
    EConst,
    EApp,
    ENat,
    EVar,
    intro,
)
from poussins.errors import KernelTypeError
from poussins.kernel import Context, ProofEngine, infer_expr
from poussins.tactics import cases, trivial


NAT = "Nat"
PROP = "Prop"


def test_forall_intro_then_refl_closes_goal():
    goal = EForall("n", NAT, EEq(EVar("n"), EVar("n")))
    engine = ProofEngine(goal)
    engine.goal.context = engine.goal.context.add_sorts({"Nat": NAT})

    intro(engine, "k")
    engine.close_goal(PRefl(EVar("k")))

    assert engine.is_closed


def test_forall_elim_substitutes_witness_term():
    ctx = Context(
        hyp_ctx={"h": EForall("n", NAT, EEq(EVar("n"), EVar("n")))},
        term_ctx={},
    ).add_sorts({"Nat": NAT})

    inferred = infer_expr(PForallE(PVar("h"), ENat(2)), ctx)

    assert inferred == EEq(ENat(2), ENat(2))


def test_cases_destructs_existential_hypothesis():
    goal = EImp(
        EExists("n", NAT, EEq(EVar("n"), EVar("n"))),
        ETop(),
    )
    engine = ProofEngine(goal)
    engine.goal.context = engine.goal.context.add_sorts({"Nat": NAT})

    intro(engine, "hex")
    cases(engine, "hex", ("w", "hw"))
    trivial(engine, None)

    assert engine.is_closed


def test_sort_mismatch_is_rejected():
    ctx = Context(hyp_ctx={}, term_ctx={"x": NAT}).add_sorts({"Nat": NAT, "Prop": PROP})

    with pytest.raises(KernelTypeError):
        infer_expr(PRefl(EApp("succ", (EConst("p", PROP),))), ctx)


def test_user_defined_sort_requires_declaration():
    person = "Person"
    term = EConst("alice", person)

    with pytest.raises(KernelTypeError):
        infer_expr(PRefl(term), Context(hyp_ctx={}, term_ctx={}))


def test_user_defined_sort_works_when_declared():
    person = "Person"
    term = EConst("alice", person)
    ctx = Context(hyp_ctx={}, term_ctx={}).add_sorts({"Person": person})

    assert infer_expr(PRefl(term), ctx) == EEq(term, term)


def test_nat_symbols_are_provided_by_environment_prelude():
    env = Environment.with_nat_prelude()
    ctx = env.extend_context(Context(hyp_ctx={}, term_ctx={}))
    term = EApp("succ", (ENat(0),))

    assert infer_expr(PRefl(term), ctx) == EEq(term, term)


def test_environment_add_dispatcher_accepts_multiple_entry_types():
    env = Environment()
    person = "Person"
    env.add(("Person", person))
    env.add(FunctionSymbol("id_person", (person,), person))
    env.add(PredicateSymbol("is_adult", (person,)))

    ctx = env.extend_context(Context(hyp_ctx={}, term_ctx={}))
    term = EApp("id_person", (EConst("alice", person),))

    assert infer_expr(PRefl(term), ctx) == EEq(term, term)
