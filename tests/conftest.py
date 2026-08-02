import pytest

from poussins.environment import Environment


@pytest.fixture
def default_env() -> Environment:
    return Environment.default()
