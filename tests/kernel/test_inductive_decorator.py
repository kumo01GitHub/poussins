"""Behavioral tests for the inductive type decorator."""

from poussins.ast import EConst, Sort
from poussins.environment import InductiveSpec
from poussins.framework import create_environment
from poussins.framework.inductive import Inductive, inductive_type


def test_declare_sets_env_only_for_target_class():
    """Declaring one custom inductive should not mutate another class env."""
    my_nat_spec = InductiveSpec(
        name="MyNat",
        type=Sort.TYPE.sort,
        constructors=(("MyNat.zero", EConst("MyNat", ())),),
    )
    my_bool_spec = InductiveSpec(
        name="MyBool",
        type=Sort.TYPE.sort,
        constructors=(("MyBool.true", EConst("MyBool", ())),),
    )

    @inductive_type(spec=my_nat_spec)
    class MyNat(Inductive):
        pass

    @inductive_type(spec=my_bool_spec)
    class MyBool(Inductive):
        pass

    env_nat = create_environment()
    env_bool = create_environment()

    MyNat.declare(env_nat)
    assert MyNat.env() is env_nat
    assert MyBool.env() is None

    MyBool.declare(env_bool)
    assert MyNat.env() is env_nat
    assert MyBool.env() is env_bool
