# -*- coding: utf-8 -*-
"""
Crawler configuration for Tribeca Insights.

Defines crawl delay handling, robots.txt parsing, the USER_AGENT string,
supported languages, HTTP session setup and SSL workaround for NLTK.
"""

import os
import logging
from urllib import robotparser
from urllib.error import URLError
from urllib.parse import urljoin

import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import requests

logger = logging.getLogger(__name__)


crawl_delay: float = 0.0
# Default HTTP request timeout in seconds
HTTP_TIMEOUT: int = 10

# Supported language codes for stopwords and tokenization
SUPPORTED_LANGUAGES = ["en", "pt-br", "es", "fr", "it", "de", "zh-cn", "ja", "ru", "ar"]


def get_crawl_delay(base_url: str) -> float:
    """Return the crawl-delay defined in robots.txt for our user agent.

    Attempts to read the delay for ``tribeca-insights`` first, then ``*``.
    Falls back to the default value if missing or on read failure.
    """
    parser = robotparser.RobotFileParser()
    parser.set_url(urljoin(base_url, "/robots.txt"))
    try:
        parser.read()
        delay = parser.crawl_delay("tribeca-insights")
        if delay is None:
            delay = parser.crawl_delay("*")
        return delay or crawl_delay
    except (URLError, IOError) as e:
        logger.warning(f"Error reading robots.txt crawl-delay: {e}")
        return crawl_delay


VERSION: str = "1.0"
USER_AGENT: str = f"tribeca-insights/{VERSION}"
CRAWLED_BY: str = USER_AGENT

# Default session used for all crawler HTTP requests
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})
