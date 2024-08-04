import pytest
from tests.utils import get, post


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["benchmark"])
def test_validate_get(function_type: str, session):
    res = get(f"/{function_type}/validate")
    assert res.status_code == 200


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["benchmark"])
def test_validate_post(function_type: str, session):
    res = post(f"/{function_type}/validate", data={"name": "John", "age": 25})
    assert res.status_code == 200
