"""
Crawler configuration for Tribeca Insights.

Defines default crawl delay, robots.txt parsing, USER_AGENT, supported languages, and HTTP session.
"""

from urllib.parse import urljoin
from urllib import robotparser
import requests

crawl_delay = 0.0

# Supported language codes for stopwords and tokenization
SUPPORTED_LANGUAGES = [
    "en", "pt-br", "es", "fr", "it", "de",
    "zh-cn", "ja", "ru", "ar"
]

def get_crawl_delay(base_url: str) -> float:
    """Fetch crawl-delay from robots.txt or return default crawl_delay."""
    parser = robotparser.RobotFileParser()
    parser.set_url(urljoin(base_url, '/robots.txt'))
    try:
        parser.read()
        delay = parser.crawl_delay('tribeca-insights')
        if delay is None:
            delay = parser.crawl_delay('*')
        return delay or crawl_delay
    except Exception:
        return crawl_delay
VERSION = '1.0'
USER_AGENT = f"tribeca-insights/{VERSION}"
CRAWLED_BY = USER_AGENT
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})