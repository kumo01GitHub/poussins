import pytest

from poussins.ast import EConst, ESort, UnivLevelZero, UnivLevelSucc
from poussins.environment import Environment


@pytest.fixture
def prop() -> ESort:
    return ESort(UnivLevelZero())


@pytest.fixture
def type1() -> ESort:
    return ESort(UnivLevelSucc(UnivLevelZero()))


@pytest.fixture
def true_const() -> EConst:
    return EConst("True", ())


@pytest.fixture
def true_intro_const() -> EConst:
    return EConst("True.intro", ())


@pytest.fixture
def default_env() -> Environment:
    return Environment.default()
