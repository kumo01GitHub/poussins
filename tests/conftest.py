import pytest

from poussins.environment import Environment


@pytest.fixture
def standard_env() -> Environment:
    return Environment.standard()
