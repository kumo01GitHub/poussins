"""Standard declarations."""
from .bool import BOOL_IND_SPEC
from .empty import EMPTY_IND_SPEC
from .equality import EQ_IND_SPEC, EQ_SYMM_DEF_SPEC, EQ_TRANS_DEF_SPEC
from .fin import FIN_IND_SPEC
from .list import LIST_IND_SPEC
from .logic import AND_IND_SPEC, EXISTS_IND_SPEC, FALSE_IND_SPEC, NOT_DEF_SPEC, OR_IND_SPEC, TRUE_IND_SPEC
from .nat import NAT_ADD_DEF_SPEC, NAT_DIV_DEF_SPEC, NAT_IND_SPEC, NAT_MOD_DEF_SPEC, NAT_MUL_DEF_SPEC, NAT_SUB_DEF_SPEC
from .option import OPTION_IND_SPEC
from .prod import PROD_IND_SPEC
from .quot import (
    QUOT_DECLARATION,
    QUOT_IND_DECLARATION,
    QUOT_LIFT_DECLARATION,
    QUOT_MK_DECLARATION,
    QUOT_SOUND_DECLARATION,
)
from .sigma import SIGMA_IND_SPEC
from .sum import SUM_IND_SPEC
from .unit import UNIT_IND_SPEC
from .vector import VECTOR_IND_SPEC

__all__ = [
    # Inductive declarations
    "EQ_IND_SPEC",
    "EQ_SYMM_DEF_SPEC",
    "EQ_TRANS_DEF_SPEC",
    "TRUE_IND_SPEC", "FALSE_IND_SPEC", "AND_IND_SPEC", "OR_IND_SPEC", "NOT_DEF_SPEC", "EXISTS_IND_SPEC",
    "EMPTY_IND_SPEC",
    "UNIT_IND_SPEC",
    "BOOL_IND_SPEC",
    "NAT_IND_SPEC", "NAT_ADD_DEF_SPEC", "NAT_SUB_DEF_SPEC", "NAT_MUL_DEF_SPEC", "NAT_DIV_DEF_SPEC", "NAT_MOD_DEF_SPEC",
    "LIST_IND_SPEC",
    "VECTOR_IND_SPEC",
    "FIN_IND_SPEC",
    "PROD_IND_SPEC",
    "SIGMA_IND_SPEC",
    "SUM_IND_SPEC",
    "OPTION_IND_SPEC",
    # Quotient declarations
    "QUOT_DECLARATION",
    "QUOT_MK_DECLARATION",
    "QUOT_LIFT_DECLARATION",
    "QUOT_IND_DECLARATION",
    "QUOT_SOUND_DECLARATION",
]
