import pytest
from tests.utils import multipart_post


# json
@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["benchmark"])
def test_json(function_type: str, session):
    res = multipart_post(f"/{function_type}/json")
    assert res.status_code == 200
    assert res.json()


# html
@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["benchmark"])
def test_html(function_type: str, session):
    res = multipart_post(f"/{function_type}/html")
    assert res.status_code == 200
    assert res.text == "<h1>Hello World!</h1>"


# plain text
@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["benchmark"])
def test_plain_text(function_type: str, session):
    res = multipart_post(f"/{function_type}/plain_text")
    assert res.status_code == 200
    assert res.text == "Hello World!"


# redirect
@pytest.mark.benchmark
@pytest.mark.parametrize("function_type", ["benchmark"])
def test_redirect(function_type: str, session):
    res = multipart_post(f"/{function_type}/redirect")
    assert res.status_code == 200
    assert "benchmark/default" in res.url
