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
from .quot import QuotLibraryDeclaration
from .sigma import SigmaDeclaration
from .sort import Sort
from .sum import SumDeclaration
from .unit import UnitDeclaration
from .vector import VectorDeclaration

__all__ = [
    "BoolDeclaration",
    "EmptyDeclaration",
    "EqualityDeclaration",
    "FinDeclaration",
    "ListDeclaration",
    "LogicDeclaration",
    "NatDeclaration",
    "OptionDeclaration",
    "ProdDeclaration",
    "QuotLibraryDeclaration",
    "SigmaDeclaration",
    "Sort",
    "SumDeclaration",
    "UnitDeclaration",
    "VectorDeclaration",
    "EQ_APP_ARITY",
]
