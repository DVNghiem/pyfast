import pytest
from tests.utils import multipart_post


@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["benchmark"])
def test_form_data(function_type: str, session):
    res = multipart_post(f"/{function_type}/file", files={"hello": "world"})
    assert "multipart" in res.text
