import pytest
from tests.utils import get


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type,type", [("benchmark", "sync"), ("benchmark", "async")])
def test_sync_async(function_type: str, type: str, session):
    res = get(f"/{function_type}/{type}")
    assert res.status_code == 200
