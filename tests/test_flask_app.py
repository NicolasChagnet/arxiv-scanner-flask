""" Testing for the main flask app file """
import pytest
from arxiv_scanner_flask import flask_app


@pytest.mark.parametrize("date_str, dateformat, expected_result", [
    ("2024-01-27", "%Y-%m-%d", True),
    ("2024-27-01", "%Y-%m-%d", False),
    ("", "%Y-%m-%d", False),
    ("2024-01-27", "%Y%m%d", False),
    ("20240127", "%Y%m%d", True)
])
def test_validate_date(date_str, dateformat, expected_result):
    """ Tests that the date validation function """
    assert flask_app.validate_date(date_str, dateformat) == expected_result


@pytest.mark.parametrize("link, expected_result", [
    ("<a>Test1</a>", ["Test1"]),
    ("<a>Test2", []),
    ("<a href=\"http://google.com\">Test3</a>", ["Test3"]),
    ("<a href=\"http://google.com\">Test4</a> and also <a href=\"http://google.com\" id=\"Hello\">Test5</a>",
     ["Test4", "Test5"])
])
def test_format_link(link, expected_result):
    """ Tests various HTML links """
    assert flask_app.format_link(link) == expected_result


@pytest.mark.parametrize("title, expected_result", [
    ("Some paper", "Some paper"),
    ("Some paper arXiv:2401.00000", "Some paper"),
    ("arXiv:2333.0000", ""),
    ("Some paper about arXiv papers arXiv:2401.0000", "Some paper about arXiv papers")
])
def test_treat_title(title, expected_result):
    """ Tests various HTML links """
    assert flask_app.treat_title(title) == expected_result


@pytest.mark.parametrize("link, expected_result", [
    ("https://arxiv.org/abs/2303.17685", "2303.17685"),
    ("https://arxiv.org/abs/cond-mat/9510129", "cond-mat/9510129"),
    ("https://arxiv.org", ""),
    ("https://arxiv.org/abs/", "")
])
def test_extract_identifier(link, expected_result):
    """ Tests various HTML links """
    assert flask_app.extract_identifier(link) == expected_result
