"""Standard declarations."""
from .bool import BoolDeclaration
from .empty import EmptyDeclaration
from .equality import EqualityDeclaration
from .fin import FinDeclaration
from .list import ListDeclaration
from .logic import LogicDeclaration
from .nat import NatDeclaration
from .option import OptionDeclaration
from .prod import ProdDeclaration
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
    "Sort",
    "SumDeclaration",
    "UnitDeclaration",
    "VectorDeclaration",
]
