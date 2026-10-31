"""Environment factories."""
from ..environment import Environment
from ..environment.library import (
    AND_IND_SPEC,
    BOOL_IND_SPEC,
    EMPTY_IND_SPEC,
    EQ_IND_SPEC,
    EQ_SYMM_DEF_SPEC,
    EQ_TRANS_DEF_SPEC,
    EXISTS_IND_SPEC,
    FALSE_IND_SPEC,
    FIN_IND_SPEC,
    LIST_IND_SPEC,
    NAT_ADD_DEF_SPEC,
    NAT_DIV_DEF_SPEC,
    NAT_IND_SPEC,
    NAT_MOD_DEF_SPEC,
    NAT_MUL_DEF_SPEC,
    NAT_SUB_DEF_SPEC,
    NOT_DEF_SPEC,
    OPTION_IND_SPEC,
    OR_IND_SPEC,
    PROD_IND_SPEC,
    SIGMA_IND_SPEC,
    SUM_IND_SPEC,
    TRUE_IND_SPEC,
    UNIT_IND_SPEC,
    VECTOR_IND_SPEC,
)
from .declaration import declare_definition, declare_inductive, declare_quot


def create_environment() -> Environment:
    """Create an empty environment."""
    return Environment()


def create_standard_environment() -> Environment:
    """Create a standard environment with common declarations."""
    env = Environment()

    # ------------------------------------------------------------------
    # Equality
    # ------------------------------------------------------------------
    declare_inductive(env, EQ_IND_SPEC)
    declare_definition(env, EQ_SYMM_DEF_SPEC)
    declare_definition(env, EQ_TRANS_DEF_SPEC)

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------
    declare_inductive(env, TRUE_IND_SPEC)
    declare_inductive(env, FALSE_IND_SPEC)
    declare_inductive(env, AND_IND_SPEC)
    declare_inductive(env, OR_IND_SPEC)
    declare_definition(env, NOT_DEF_SPEC)
    declare_inductive(env, EXISTS_IND_SPEC)

    # ------------------------------------------------------------------
    # Empty
    # ------------------------------------------------------------------
    declare_inductive(env, EMPTY_IND_SPEC)

    # ------------------------------------------------------------------
    # Unit
    # ------------------------------------------------------------------
    declare_inductive(env, UNIT_IND_SPEC)

    # ------------------------------------------------------------------
    # Boolean
    # ------------------------------------------------------------------
    declare_inductive(env, BOOL_IND_SPEC)

    # ------------------------------------------------------------------
    # Natural numbers
    # ------------------------------------------------------------------
    declare_inductive(env, NAT_IND_SPEC)
    declare_definition(env, NAT_ADD_DEF_SPEC)
    declare_definition(env, NAT_SUB_DEF_SPEC)
    declare_definition(env, NAT_MUL_DEF_SPEC)
    declare_definition(env, NAT_DIV_DEF_SPEC)
    declare_definition(env, NAT_MOD_DEF_SPEC)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------
    declare_inductive(env, LIST_IND_SPEC)

    # ------------------------------------------------------------------
    # Vector
    # ------------------------------------------------------------------
    declare_inductive(env, VECTOR_IND_SPEC)

    # ------------------------------------------------------------------
    # Finite
    # ------------------------------------------------------------------
    declare_inductive(env, FIN_IND_SPEC)

    # ------------------------------------------------------------------
    # Product
    # ------------------------------------------------------------------
    declare_inductive(env, PROD_IND_SPEC)

    # ------------------------------------------------------------------
    # Sigma
    # ------------------------------------------------------------------
    declare_inductive(env, SIGMA_IND_SPEC)

    # ------------------------------------------------------------------
    # Sum
    # ------------------------------------------------------------------
    declare_inductive(env, SUM_IND_SPEC)

    # ------------------------------------------------------------------
    # Option
    # ------------------------------------------------------------------
    declare_inductive(env, OPTION_IND_SPEC)

    # ------------------------------------------------------------------
    # Quotient
    # ------------------------------------------------------------------
    declare_quot(env)

    return env


STANDARD_ENV = create_standard_environment()
