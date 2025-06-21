"""
Crawler configuration for Tribeca Insights.

Defines default crawl delay, robots.txt parsing, USER_AGENT, supported languages, and HTTP session.
"""

from urllib.parse import urljoin
from urllib import robotparser
from urllib.error import URLError
import requests
import logging

logger = logging.getLogger(__name__)


crawl_delay: float = 0.0
# Default HTTP request timeout in seconds
HTTP_TIMEOUT: int = 10

# Supported language codes for stopwords and tokenization
SUPPORTED_LANGUAGES = [
    "en", "pt-br", "es", "fr", "it", "de",
    "zh-cn", "ja", "ru", "ar"
]

def get_crawl_delay(base_url: str) -> float:
    """
    Retrieve crawl-delay from robots.txt for 'tribeca-insights' user-agent, 
    fallback to wildcard (*), then to default if unset or on error.
    """
    parser = robotparser.RobotFileParser()
    parser.set_url(urljoin(base_url, '/robots.txt'))
    try:
        parser.read()
        delay = parser.crawl_delay('tribeca-insights')
        if delay is None:
            delay = parser.crawl_delay('*')
        return delay or crawl_delay
    except (URLError, IOError) as e:
        logger.warning(f"Error reading robots.txt crawl-delay: {e}")
        return crawl_delay

VERSION: str = '1.0'
USER_AGENT: str = f"tribeca-insights/{VERSION}"
CRAWLED_BY: str = USER_AGENT

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})