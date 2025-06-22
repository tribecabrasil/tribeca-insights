"""Playwright-based HTML fetcher for dynamic pages."""

from typing import Optional


def fetch_with_playwright(url: str, timeout: int) -> str:
    """Return rendered HTML for ``url`` using Playwright.

    Args:
        url: Page URL.
        timeout: Timeout in seconds for page load.

    Returns:
        The page HTML after rendering dynamic content.
    """
    from playwright.sync_api import sync_playwright

    html: Optional[str] = None
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout * 1000)
        html = page.content()
        browser.close()
    return html or ""
