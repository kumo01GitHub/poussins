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
    EApp,
    EVar,
    intro,
)
from poussins.errors import KernelTypeError
from poussins.kernel import Context, ProofEngine, infer_expr
from poussins.tactics import cases, trivial


NAT = "Nat"
PROP = "Prop"


def nat_lit(value: int):
    if value < 0:
        raise ValueError("Natural number literals must be non-negative.")

    term = EApp("zero", ())
    for _ in range(value):
        term = EApp("succ", (term,))
    return term


def test_forall_intro_then_refl_closes_goal():
    goal = EForall("n", NAT, EEq(EVar("n"), EVar("n")))
    engine = ProofEngine(goal)
    engine.goal.context = engine.goal.context.add_sorts({"Nat": NAT})

    intro(engine, "k")
    engine.close_goal(PRefl(EVar("k")))

    assert engine.is_closed


def test_forall_elim_substitutes_witness_term():
    ctx = Environment.with_nat_prelude().extend_context(
        Context(
            hyp_ctx={"h": EForall("n", NAT, EEq(EVar("n"), EVar("n")))},
            term_ctx={},
        )
    )
    two = nat_lit(2)

    inferred = infer_expr(PForallE(PVar("h"), two), ctx)

    assert inferred == EEq(two, two)


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
    ctx = Environment.with_nat_prelude().extend_context(
        Context(hyp_ctx={}, term_ctx={"x": NAT}).add_sorts({"Prop": PROP})
    ).add_fn_symbols({"p": FunctionSymbol("p", (), PROP)})

    with pytest.raises(KernelTypeError):
        infer_expr(PRefl(EApp("succ", (EApp("p", ()),))), ctx)


def test_user_defined_sort_requires_declaration():
    person = "Person"
    term = EApp("alice", ())

    with pytest.raises(KernelTypeError):
        infer_expr(PRefl(term), Context(hyp_ctx={}, term_ctx={}))


def test_user_defined_sort_works_when_declared():
    person = "Person"
    term = EApp("alice", ())
    ctx = Context(hyp_ctx={}, term_ctx={}).add_sorts({"Person": person}).add_fn_symbols(
        {"alice": FunctionSymbol("alice", (), person)}
    )

    assert infer_expr(PRefl(term), ctx) == EEq(term, term)


def test_nat_symbols_are_provided_by_environment_prelude():
    env = Environment.with_nat_prelude()
    ctx = env.extend_context(Context(hyp_ctx={}, term_ctx={}))
    term = EApp("succ", (nat_lit(0),))

    assert infer_expr(PRefl(term), ctx) == EEq(term, term)


def test_environment_add_dispatcher_accepts_multiple_entry_types():
    env = Environment()
    person = "Person"
    env.add(("Person", person))
    env.add(FunctionSymbol("alice", (), person))
    env.add(FunctionSymbol("id_person", (person,), person))
    env.add(FunctionSymbol("is_adult", (person,), "Prop"))

    ctx = env.extend_context(Context(hyp_ctx={}, term_ctx={}))
    term = EApp("id_person", (EApp("alice", ()),))

    assert infer_expr(PRefl(term), ctx) == EEq(term, term)
