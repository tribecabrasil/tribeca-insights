import time

import pandas as pd
import pytest
from bs4 import BeautifulSoup

import tribeca_insights.crawler as crawler


def test_get_external_links():
    html = '<a href="https://ext.com">ex</a><a href="https://mysite.com">in</a>'
    soup = BeautifulSoup(html, "html.parser")
    links = crawler.get_external_links(soup, "mysite.com")
    assert links == {"https://ext.com"}


def test_extract_page_metadata():
    html = (
        "<html><head><title>T</title><meta name='description' content='d'></head>"
        "<body><h1>H1</h1><h2>H2</h2></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    (slug_title, headings, desc) = crawler._extract_page_metadata(
        soup, "https://mysite.com/path", "mysite.com"
    )
    assert slug_title == ("path", "T")
    assert desc == "d"
    assert headings == ["# H1", "## H2"]


def test_collect_media_and_links():
    html = (
        "<img src='img.png' alt='a'><a href='https://ext.com'>e</a>"
        "<a href='https://mysite.com/page'>in</a>"
    )
    soup = BeautifulSoup(html, "html.parser")
    images, external = crawler._collect_media_and_links(soup, "mysite.com")
    assert images == [{"src": "img.png", "alt": "a"}]
    assert external == {"https://ext.com"}


def test_fetch_and_process(monkeypatch, tmp_path):
    html = (
        "<html><head><title>T</title><meta name='description' content='d'></head>"
        "<body><h1>H1</h1><p>body</p><a href='https://ext.com'>e</a></body></html>"
    )

    class FakeResp:
        def __init__(self, text: str):
            self.text = text

    monkeypatch.setattr(crawler.session, "get", lambda url, timeout: FakeResp(html))
    monkeypatch.setattr(crawler, "export_page_to_markdown", lambda *a, **k: None)
    monkeypatch.setattr(crawler, "extract_visible_text", lambda t: "Body text")
    monkeypatch.setattr(
        crawler, "clean_and_tokenize", lambda t, _lang: ["body", "text"]
    )
    monkeypatch.setattr(time, "sleep", lambda s: None)

    vis, ext, index, md, data = crawler.fetch_and_process(
        "https://mysite.com", "mysite.com", tmp_path, "en", timeout=1, fetch_fn=None
    )
    assert vis == "Body text"
    assert ext == {"https://ext.com"}
    assert md == "home.md"
    assert data["title"] == "T"


def test_fetch_and_process_error(monkeypatch, tmp_path):
    class FakeResp:
        def __init__(self, text: str):
            self.text = text

    monkeypatch.setattr(
        crawler.session, "get", lambda url, timeout: FakeResp("<html></html>")
    )
    monkeypatch.setattr(time, "sleep", lambda s: None)

    def boom(*_a, **_k) -> None:
        raise ValueError("fail")

    monkeypatch.setattr(crawler, "export_page_to_markdown", boom)

    with pytest.raises(crawler.PageProcessingError):
        crawler.fetch_and_process(
            "https://mysite.com", "mysite.com", tmp_path, fetch_fn=None
        )


def test_crawl_site_use_playwright_flag(monkeypatch, tmp_path):
    df = pd.DataFrame(
        {
            "URL": ["https://a", "https://b"],
            "Status": [2, 2],
            "Data": "",
            "MD File": "",
            "JSON File": "",
        }
    )
    called = {}

    def spy_fetch(*args, **kwargs):
        called["fn"] = args[5] if len(args) > 5 else kwargs.get("fetch_fn")
        return "", set(), ("", ""), "", {}

    monkeypatch.setattr(crawler, "fetch_and_process", spy_fetch)
    monkeypatch.setattr(crawler, "save_visited_urls", lambda *a, **k: None)
    monkeypatch.setattr(crawler, "export_external_urls", lambda *a, **k: None)

    crawler.crawl_site(
        "mysite",
        "https://mysite.com",
        tmp_path,
        df,
        max_pages=2,
        use_playwright=True,
    )
    assert called["fn"] is not None


def test_crawl_site_use_playwright_many_pages(monkeypatch, tmp_path):
    df = pd.DataFrame(
        {
            "URL": [f"https://a/{i}" for i in range(4)],
            "Status": [2, 2, 2, 2],
            "Data": "",
            "MD File": "",
            "JSON File": "",
        }
    )
    called = {}

    def spy_fetch(*args, **kwargs):
        called["fn"] = args[5] if len(args) > 5 else kwargs.get("fetch_fn")
        return "", set(), ("", ""), "", {}

    monkeypatch.setattr(crawler, "fetch_and_process", spy_fetch)
    monkeypatch.setattr(crawler, "save_visited_urls", lambda *a, **k: None)
    monkeypatch.setattr(crawler, "export_external_urls", lambda *a, **k: None)

    crawler.crawl_site(
        "mysite",
        "https://mysite.com",
        tmp_path,
        df,
        max_pages=4,
    )
    assert called["fn"] is not None
