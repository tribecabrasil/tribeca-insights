import logging
import sys
import types
from pathlib import Path

from tribeca_insights import crawler, playwright_crawler


def test_fetch_with_playwright_timeout(monkeypatch, caplog):
    class DummyTimeoutError(Exception):
        pass

    class DummyPage:
        def goto(self, url: str, timeout: int) -> None:
            raise DummyTimeoutError("timeout")

        def content(self) -> str:
            return "<html></html>"

    class DummyBrowser:
        def new_page(self) -> DummyPage:
            return DummyPage()

        def close(self) -> None:
            pass

    class DummyPlaywright:
        def __init__(self) -> None:
            self.firefox = self

        def launch(self, headless: bool = True) -> DummyBrowser:
            return DummyBrowser()

    class DummyContext:
        def __enter__(self) -> DummyPlaywright:
            return DummyPlaywright()

        def __exit__(self, exc_type, exc, tb) -> None:
            pass

    def fake_sync_playwright() -> DummyContext:
        return DummyContext()

    fake_module = types.ModuleType("playwright.sync_api")
    fake_module.sync_playwright = fake_sync_playwright
    fake_module.Error = DummyTimeoutError
    fake_module.TimeoutError = DummyTimeoutError
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_module)

    caplog.set_level(logging.ERROR, logger="tribeca_insights.playwright_crawler")
    html = playwright_crawler.fetch_with_playwright("https://example.com", 1)
    assert html == ""
    assert any("Playwright error" in r.message for r in caplog.records)


def test_fetch_and_process_empty_html(monkeypatch, tmp_path: Path, caplog):
    caplog.set_level(logging.ERROR, logger="tribeca_insights.crawler")
    monkeypatch.setattr(crawler, "export_page_to_markdown", lambda *a, **k: None)
    monkeypatch.setattr(crawler.time, "sleep", lambda s: None)

    result = crawler.fetch_and_process(
        "https://example.com", "example.com", tmp_path, fetch_fn=lambda *_a: ""
    )
    assert result == ("", set(), ("", ""), "", {})
    assert any("No HTML returned" in r.message for r in caplog.records)


def test_fetch_with_playwright_returns_html(monkeypatch):
    html = "<html><body>Hello</body></html>"

    class DummyPage:
        def goto(self, url: str, timeout: int) -> None:
            self.url = url

        def content(self) -> str:
            return html

    class DummyBrowser:
        def new_page(self) -> DummyPage:
            return DummyPage()

        def close(self) -> None:
            pass

    class DummyPlaywright:
        def __init__(self) -> None:
            self.firefox = self

        def launch(self, headless: bool = True) -> DummyBrowser:
            return DummyBrowser()

    class DummyContext:
        def __enter__(self) -> DummyPlaywright:
            return DummyPlaywright()

        def __exit__(self, exc_type, exc, tb) -> None:
            pass

    def fake_sync_playwright() -> DummyContext:
        return DummyContext()

    fake_module = types.ModuleType("playwright.sync_api")
    fake_module.sync_playwright = fake_sync_playwright
    fake_module.Error = Exception
    fake_module.TimeoutError = Exception
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_module)

    result = playwright_crawler.fetch_with_playwright("https://example.com", 1)
    assert result == html


def test_fetch_with_playwright_error_logging(monkeypatch, caplog):
    class DummyError(Exception):
        pass

    class DummyPage:
        def goto(self, url: str, timeout: int) -> None:
            raise DummyError("fail")

        def content(self) -> str:
            return ""

    class DummyBrowser:
        def new_page(self) -> DummyPage:
            return DummyPage()

        def close(self) -> None:
            pass

    class DummyPlaywright:
        def __init__(self) -> None:
            self.firefox = self

        def launch(self, headless: bool = True) -> DummyBrowser:
            return DummyBrowser()

    class DummyContext:
        def __enter__(self) -> DummyPlaywright:
            return DummyPlaywright()

        def __exit__(self, exc_type, exc, tb) -> None:
            pass

    def fake_sync_playwright() -> DummyContext:
        return DummyContext()

    fake_module = types.ModuleType("playwright.sync_api")
    fake_module.sync_playwright = fake_sync_playwright
    fake_module.Error = DummyError
    fake_module.TimeoutError = DummyError
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_module)

    caplog.set_level(logging.ERROR, logger="tribeca_insights.playwright_crawler")
    html = playwright_crawler.fetch_with_playwright("https://example.com", 1)
    assert html == ""
    assert any("Playwright error" in r.message for r in caplog.records)
