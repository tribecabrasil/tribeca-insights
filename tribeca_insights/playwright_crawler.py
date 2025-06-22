"""Playwright-based HTML fetcher for dynamic pages."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def fetch_with_playwright(url: str, timeout: int) -> str:
    """Return rendered HTML for ``url`` using Playwright.

    Args:
        url: Page URL.
        timeout: Timeout in seconds for page load.

    Returns:
        The page HTML after rendering dynamic content, or an empty string on
        failure.
    """
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:  # pragma: no cover - environment issue
        logger.error(
            "Playwright is required. Run 'pip install playwright' and 'playwright install'."
        )
        return ""

    html: Optional[str] = None
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=timeout * 1000)
            html = page.content()
        except (
            PlaywrightError,
            PlaywrightTimeoutError,
        ) as exc:  # pragma: no cover - mocked in tests
            logger.error("Playwright error for %s: %s", url, exc)
            return ""
        finally:
            if browser:
                browser.close()
    return html or ""
