import logging
import sys
import types

from tribeca_insights.playwright_crawler import fetch_with_playwright


class DummyTimeoutError(Exception):
    pass


class DummyPage:
    def __init__(self, html: str, raise_exc: bool = False) -> None:
        self._html = html
        self._raise_exc = raise_exc

    def goto(self, url: str, timeout: int) -> None:
        if self._raise_exc:
            raise DummyTimeoutError("timeout")

    def content(self) -> str:
        return self._html


class DummyBrowser:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def new_page(self) -> DummyPage:
        return self._page

    def close(self) -> None:
        pass


class DummyPlaywright:
    def __init__(self, page: DummyPage) -> None:
        self.firefox = self
        self._page = page

    def launch(self, headless: bool = True) -> DummyBrowser:
        return DummyBrowser(self._page)


class DummyContext:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def __enter__(self) -> DummyPlaywright:
        return DummyPlaywright(self._page)

    def __exit__(self, exc_type, exc, tb) -> None:
        pass


def _patch_playwright(monkeypatch, page: DummyPage) -> None:
    def fake_sync_playwright() -> DummyContext:
        return DummyContext(page)

    fake_module = types.ModuleType("playwright.sync_api")
    fake_module.sync_playwright = fake_sync_playwright
    fake_module.Error = DummyTimeoutError
    fake_module.TimeoutError = DummyTimeoutError
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_module)


def test_fetch_returns_html(monkeypatch):
    html = "<html><body>OK</body></html>"
    _patch_playwright(monkeypatch, DummyPage(html))

    result = fetch_with_playwright("https://example.com", timeout=1)
    assert result == html


def test_fetch_logs_timeout(monkeypatch, caplog):
    _patch_playwright(monkeypatch, DummyPage("", raise_exc=True))

    caplog.set_level(logging.ERROR, logger="tribeca_insights.playwright_crawler")
    result = fetch_with_playwright("https://example.com", timeout=1)

    assert result == ""
    assert any("Playwright error" in r.message for r in caplog.records)
