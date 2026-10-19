"""Standard declarations."""
from .bool import BoolDeclaration
from .empty import EmptyDeclaration
from .equality import EQ_APP_ARITY, EqualityDeclaration
from .fin import FinDeclaration
from .list import ListDeclaration
from .logic import LogicDeclaration
from .nat import NatDeclaration
from .option import OptionDeclaration
from .prod import ProdDeclaration
from .quot import QuotDeclaration
from .sigma import SigmaDeclaration
from .sum import SumDeclaration
from .unit import UnitDeclaration
from .vector import VectorDeclaration

__all__ = [
    "EmptyDeclaration",
    "UnitDeclaration",
    "BoolDeclaration",
    "EqualityDeclaration",
    "EQ_APP_ARITY",
    "LogicDeclaration",
    "NatDeclaration",
    "ListDeclaration",
    "VectorDeclaration",
    "FinDeclaration",
    "ProdDeclaration",
    "SigmaDeclaration",
    "SumDeclaration",
    "OptionDeclaration",
    "QuotDeclaration",
]
