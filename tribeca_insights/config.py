import os
import re
import logging
from pathlib import Path

crawl_delay = 0.0

def get_crawl_delay(base_url: str) -> float:
    """Fetch crawl-delay from robots.txt or return 0."""
    parser = robotparser.RobotFileParser()
    parser.set_url(urljoin(base_url, '/robots.txt'))
    try:
        parser.read()
        delay = parser.crawl_delay('SeoCrawler')
        if delay is None:
            delay = parser.crawl_delay('*')
        return delay or 0.0
    except Exception:
        return 0.0
VERSION = '1.0'
USER_AGENT = f'SeoCrawler/{VERSION}'
CRAWLED_BY = USER_AGENT
session = requests.Session()