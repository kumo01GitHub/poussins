"""Environment factories."""
from ..environment import Environment
from ..environment.library import (
    BoolDeclaration,
    EmptyDeclaration,
    EqualityDeclaration,
    FinDeclaration,
    ListDeclaration,
    LogicDeclaration,
    NatDeclaration,
    OptionDeclaration,
    ProdDeclaration,
    QuotDeclaration,
    SigmaDeclaration,
    SumDeclaration,
    UnitDeclaration,
    VectorDeclaration,
)
from ..kernel import (
    declare_definition,
    declare_inductive,
    declare_quotient,
)


def create_environment() -> Environment:
    """Create an empty environment."""
    return Environment()


def create_standard_environment() -> Environment:
    """Create a standard environment with common declarations."""
    env = Environment()

    # Boolean
    declare_inductive(
        env,
        BoolDeclaration.BOOL_DECLARATION.value,
        (
            BoolDeclaration.BOOL_TRUE_DECLARATION.value,
            BoolDeclaration.BOOL_FALSE_DECLARATION.value,
        ),
        BoolDeclaration.BOOL_REC_DECLARATION.value,
    )

    # Empty
    declare_inductive(
        env,
        EmptyDeclaration.EMPTY_DECLARATION.value,
        (),
        None,
    )

    # Equality
    declare_inductive(
        env,
        EqualityDeclaration.EQ_DECLARATION.value,
        (
            EqualityDeclaration.EQ_REFL_DECLARATION.value,
        ),
        EqualityDeclaration.EQ_REC_DECLARATION.value,
    )
    declare_definition(
        env,
        EqualityDeclaration.EQ_SYMM_DECLARATION.value
    )
    declare_definition(
        env,
        EqualityDeclaration.EQ_TRANS_DECLARATION.value
    )

    # Finite
    declare_inductive(
        env,
        FinDeclaration.FIN_DECLARATION.value,
        (
            FinDeclaration.FIN_ZERO_DECLARATION.value,
            FinDeclaration.FIN_SUCC_DECLARATION.value,
        ),
        None,
    )

    # List
    declare_inductive(
        env,
        ListDeclaration.LIST_DECLARATION.value,
        (
            ListDeclaration.LIST_NIL_DECLARATION.value,
            ListDeclaration.LIST_CONS_DECLARATION.value,
        ),
        None,
    )

    # Logic
    declare_inductive(
        env,
        LogicDeclaration.TRUE_DECLARATION.value,
        (
            LogicDeclaration.TRUE_INTRO_DECLARATION.value,
        ),
        LogicDeclaration.TRUE_REC_DECLARATION.value,
    )
    declare_inductive(
        env,
        LogicDeclaration.FALSE_DECLARATION.value,
        (),
        LogicDeclaration.FALSE_REC_DECLARATION.value,
    )
    declare_inductive(
        env,
        LogicDeclaration.AND_DECLARATION.value,
        (
            LogicDeclaration.AND_INTRO_DECLARATION.value,
        ),
        LogicDeclaration.AND_REC_DECLARATION.value,
    )
    declare_inductive(
        env,
        LogicDeclaration.OR_DECLARATION.value,
        (
            LogicDeclaration.OR_INL_DECLARATION.value,
            LogicDeclaration.OR_INR_DECLARATION.value,
        ),
        LogicDeclaration.OR_REC_DECLARATION.value,
    )
    declare_definition(
        env,
        LogicDeclaration.NOT_DECLARATION.value
    )
    declare_inductive(
        env,
        LogicDeclaration.EXISTS_DECLARATION.value,
        (
            LogicDeclaration.EXISTS_INTRO_DECLARATION.value,
        ),
        LogicDeclaration.EXISTS_REC_DECLARATION.value,
    )

    # Natural numbers
    declare_inductive(
        env,
        NatDeclaration.NAT_DECLARATION.value,
        (
            NatDeclaration.NAT_ZERO_DECLARATION.value,
            NatDeclaration.NAT_SUCC_DECLARATION.value,
        ),
        NatDeclaration.NAT_REC_DECLARATION.value,
    )
    declare_definition(
        env,
        NatDeclaration.NAT_ADD_DECLARATION.value
    )

    # Option
    declare_inductive(
        env,
        OptionDeclaration.OPTION_DECLARATION.value,
        (
            OptionDeclaration.OPTION_NONE_DECLARATION.value,
            OptionDeclaration.OPTION_SOME_DECLARATION.value,
        ),
        None,
    )

    # Product
    declare_inductive(
        env,
        ProdDeclaration.PROD_DECLARATION.value,
        (
            ProdDeclaration.PROD_MK_DECLARATION.value,
        ),
        None,
    )

    # Quotient
    declare_quotient(
        env,
        QuotDeclaration.QUOT_DECLARATION.value,
        QuotDeclaration.QUOT_MK_DECLARATION.value,
        QuotDeclaration.QUOT_LIFT_DECLARATION.value,
        QuotDeclaration.QUOT_IND_DECLARATION.value
    )

    # Sigma
    declare_inductive(
        env,
        SigmaDeclaration.SIGMA_DECLARATION.value,
        (
            SigmaDeclaration.SIGMA_MK_DECLARATION.value,
        ),
        None,
    )

    # Sum
    declare_inductive(
        env,
        SumDeclaration.SUM_DECLARATION.value,
        (
            SumDeclaration.SUM_INL_DECLARATION.value,
            SumDeclaration.SUM_INR_DECLARATION.value,
        ),
        None,
    )

    # Unit
    declare_inductive(
        env,
        UnitDeclaration.UNIT_DECLARATION.value,
        (
            UnitDeclaration.UNIT_UNIT_DECLARATION.value,
        ),
        None,
    )

    # Vector
    declare_inductive(
        env,
        VectorDeclaration.VECTOR_DECLARATION.value,
        (
            VectorDeclaration.VECTOR_NIL_DECLARATION.value,
            VectorDeclaration.VECTOR_CONS_DECLARATION.value,
        ),
        None,
    )

    return env
