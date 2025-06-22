"""
Unit tests for text_utils module of Tribeca Insights.
Tests environment setup, stopwords loading, string cleaning, tokenization, and HTML text extraction.
"""

import logging
import os

import certifi
import nltk
import pytest

from tribeca_insights.text_utils import (
    _get_stopwords,
    clean_and_tokenize,
    extract_visible_text,
    safe_strip,
    setup_environment,
)


def test_setup_environment_sets_ssl_cert_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ensure setup_environment sets SSL_CERT_FILE to the certifi bundle and logs properly."""
    caplog.set_level(logging.INFO, logger="tribeca_insights.text_utils")
    setup_environment()
    assert (
        os.environ["SSL_CERT_FILE"] == certifi.where()
    ), "SSL_CERT_FILE not set to certifi bundle"
    assert any(
        "Using certifi CA bundle for SSL" in record.message for record in caplog.records
    ), "Expected log message not found"


def test_get_stopwords_caches_and_downloads(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify _get_stopwords returns stopwords and avoids unnecessary downloads."""
    called = {}

    def fake_download(name: str, quiet: bool) -> None:
        called["downloaded"] = True

    monkeypatch.setattr(nltk, "download", fake_download)
    stopwords = _get_stopwords("en")
    assert "the" in stopwords, "'the' should be in stopwords"
    assert not called.get(
        "downloaded", False
    ), "Stopwords should not be downloaded if already present"


def test_get_stopwords_spanish_mapping() -> None:
    """_get_stopwords should load Spanish stopwords for 'es' code."""
    sw = _get_stopwords("es")
    assert "y" in sw, "'y' should be a Spanish stopword"


def test_get_stopwords_portuguese_mapping() -> None:
    """_get_stopwords should load Portuguese stopwords for 'pt-br' code."""
    sw = _get_stopwords("pt-br")
    # 'e' is a common Portuguese conjunction stopword
    assert "e" in sw, "'e' should be a Portuguese stopword"


def test_safe_strip() -> None:
    """Test safe_strip trims strings and handles None or non-string inputs gracefully."""
    assert (
        safe_strip("  hello ") == "hello"
    ), "safe_strip did not trim whitespace correctly"
    assert (
        safe_strip(None) == ""
    ), "safe_strip did not return empty string for None input"
    assert safe_strip(123) == ""  # type: ignore[arg-type]


def test_clean_and_tokenize() -> None:
    """Check clean_and_tokenize removes stopwords and punctuation correctly."""
    text = "This is a test. Testing, one, two, three!"
    tokens = clean_and_tokenize(text, "en")
    assert "test" in tokens, "'test' should be in tokens"
    assert "this" not in tokens, "'this' is a stopword and should not be in tokens"


@pytest.mark.parametrize(
    "text,language,expected",
    [
        ("Numbers 123 and symbols! #$%", "en", ["numbers", "symbols"]),
        ("Mixed CASE and StopWords of the", "en", ["mixed", "case", "stopwords"]),
    ],
)
def test_clean_and_tokenize_edge_cases(
    text: str, language: str, expected: list[str]
) -> None:
    """Clean_and_tokenize should handle numbers, punctuation, and stopwords properly."""
    tokens = clean_and_tokenize(text, language)
    assert tokens == expected, f"Expected tokens {expected} but got {tokens}"


def test_extract_visible_text() -> None:
    """Ensure extract_visible_text extracts visible text and excludes scripts and styles."""
    html = "<html><head><style>body {}</style></head><body><script>alert(1);</script><p>Hello World!</p></body></html>"
    text = extract_visible_text(html)
    assert "Hello World!" in text, "'Hello World!' should be in extracted text"
    assert "alert" not in text, "'alert' from script should not be in extracted text"
    assert "body" not in text, "'body' from style should not be in extracted text"


def test_extract_visible_text_whitespace_collapse() -> None:
    """extract_visible_text should collapse multiple spaces into one."""
    html = "<p>Hello   <script>ignore</script>   World</p>"
    text = extract_visible_text(html)
    assert text == "Hello World", f"Expected 'Hello World' but got '{text}'"
