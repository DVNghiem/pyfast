import pytest
from tests.utils import get, post, put, delete


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "function_type,type,method",
    [("functional", "default", "get"), ("functional", "default", "post"), ("functional", "default", "put"), ("functional", "default", "delete")],
)
def test_sync_async(function_type: str, type: str, method: str, session):
    if method == "get":
        res = get(f"/{function_type}/{type}?name=John&age=20")
        assert res.status_code == 200
    elif method == "post":
        res = post(f"/{function_type}/{type}")
        assert res.status_code == 200
    elif method == "put":
        res = put(f"/{function_type}/{type}")
        assert res.status_code == 200
    elif method == "delete":
        res = delete(f"/{function_type}/{type}")
        assert res.status_code == 200
