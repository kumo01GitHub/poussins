from poussins.ast import EApp, EConst
from poussins.environment import ConstructorDeclaration, Environment, InductiveDeclaration
from poussins.framework import Bool, InductiveType, Nat


def test_nat_is_an_inductive_type() -> None:
    assert issubclass(Nat, InductiveType)
    assert Nat.type() == EConst(Environment.NAT_DECLARATION.name, ())
    assert Nat.eq(Nat.zero(), Nat.succ(Nat.zero())) == EApp(
        EApp(
            EApp(EConst(Environment.EQ_DECLARATION.name, ()), EConst(Environment.NAT_DECLARATION.name, ())),
            EConst(Environment.NAT_ZERO_DECLARATION.name, ()),
        ),
        EApp(EConst(Environment.NAT_SUCC_DECLARATION.name, ()), EConst(Environment.NAT_ZERO_DECLARATION.name, ())),
    )


def test_bool_wrapper_exposes_constructors() -> None:
    assert Bool.type() == EConst(Environment.BOOL_DECLARATION.name, ())
    assert Bool.true().expr == EConst(Environment.BOOL_TRUE_DECLARATION.name, ())
    assert Bool.false().expr == EConst(Environment.BOOL_FALSE_DECLARATION.name, ())


def test_default_environment_registers_bool(default_env) -> None:
    bool_decl = default_env.get("Bool")
    bool_true_decl = default_env.get("Bool.true")
    bool_false_decl = default_env.get("Bool.false")

    assert isinstance(bool_decl, InductiveDeclaration)
    assert bool_decl.type == default_env.TYPE_SORT
    assert bool_decl.constructor_names == ("Bool.true", "Bool.false")

    assert isinstance(bool_true_decl, ConstructorDeclaration)
    assert bool_true_decl.type == EConst("Bool", ())

    assert isinstance(bool_false_decl, ConstructorDeclaration)
    assert bool_false_decl.type == EConst("Bool", ())