"""
Core crawling logic for Tribeca Insights.

Defines functions to fetch and process pages concurrently, extract content,
and export results to Markdown/CSV.
"""

import concurrent.futures
import hashlib
import logging
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.packages.urllib3.util.retry import Retry
from slugify import slugify
from tqdm import tqdm

from tribeca_insights.config import HTTP_TIMEOUT, crawl_delay, session
from tribeca_insights.exporters.csv import export_external_urls
from tribeca_insights.exporters.markdown import (
    MD_PAGES_DIR,
    MD_PAGES_PLAYWRIGHT_DIR,
    export_page_to_markdown,
)
from tribeca_insights.storage import save_visited_urls
from tribeca_insights.text_utils import (
    clean_and_tokenize,
    extract_visible_text,
    safe_strip,
)

logger = logging.getLogger(__name__)


class PageProcessingError(Exception):
    """Raised when a page fails to process."""


# Configure retry policy on the shared session
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


def _extract_page_metadata(
    soup: BeautifulSoup, url: str, domain: str
) -> Tuple[Tuple[str, str], List[str], str]:
    """
    Extract title, description, and headings from a BeautifulSoup object.
    """
    # Title
    title_tag = soup.title
    title = safe_strip(title_tag.string) if title_tag else "(no title)"
    # Description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = safe_strip(desc_tag.get("content")) if desc_tag else ""
    # Headings
    headings = [
        f"{'#' * int(tag.name[1])} {tag.get_text(strip=True)}"
        for tag in soup.find_all(re.compile(r"^h[1-6]$"))
    ]
    return (slugify(urlparse(url).path or "home"), title), headings, description


def _collect_media_and_links(
    soup: BeautifulSoup, domain: str
) -> Tuple[List[Dict[str, str]], Set[str]]:
    """
    Extract images (src, alt) and external links from the page.
    """
    images = []
    for img in soup.find_all("img"):
        images.append({"src": img.get("src", ""), "alt": safe_strip(img.get("alt"))})
    external = get_external_links(soup, domain)
    return images, external


def get_external_links(soup: BeautifulSoup, domain: str) -> Set[str]:
    """
    Extract external HTTP links not containing the domain.
    """
    return {
        a["href"]
        for a in soup.find_all("a", href=True)
        if a["href"].startswith("http") and domain not in a["href"]
    }


def fetch_and_process(
    url: str,
    domain: str,
    folder: Path,
    language: str = "english",
    timeout: int = 10,
    fetch_fn=None,
) -> Tuple[str, Set[str], Tuple[str, str], str, Dict]:
    """
    Fetch and process a single page.

    Retrieves HTML, sleeps for crawl_delay, parses content, exports Markdown,
    and returns visible text, external links, index entry, markdown filename,
    and full page data for JSON export.

    :param url: URL to fetch
    :param domain: base domain slug
    :param folder: output folder Path
    :param language: language code for tokenization
    :param timeout: request timeout in seconds
    :param fetch_fn: optional callable to retrieve HTML
    :return: tuple (visible_text, external_links, index_entry, md_filename, page_data)

    :Example:
        visible_text, ext_links, index_entry, md_file, page_data = fetch_and_process(
            'https://example.com', 'example-com', Path('example-com'), 'en', timeout=10
        )
    """
    try:
        logger.info(f"Visiting URL: {url}")
        if fetch_fn is not None:
            html = fetch_fn(url, timeout)
        else:
            resp = session.get(url, timeout=timeout)
            html = resp.text
        time.sleep(crawl_delay)
        soup = BeautifulSoup(html, "html.parser")
        external_links: Set[str] = set()
        (slug, title), headings, description = _extract_page_metadata(soup, url, domain)
        images_data, external = _collect_media_and_links(soup, domain)
        external_links.update(external)
        md_filename = f"{slug}.md"
        subdir = MD_PAGES_PLAYWRIGHT_DIR if fetch_fn is not None else MD_PAGES_DIR
        export_page_to_markdown(
            folder,
            url,
            html,
            domain,
            external_links,
            subdirectory=subdir,
        )
        visible_text = extract_visible_text(html)
        tokens = clean_and_tokenize(visible_text, language)
        local_freq = Counter(tokens)
        word_freq = dict(local_freq)
        page_hash = hashlib.sha256(visible_text.encode("utf-8")).hexdigest()
        page_data = {
            "url": url,
            "slug": slug,
            "title": title,
            "meta_description": description,
            "headings": headings,
            "word_count": len(tokens),
            "word_frequency": word_freq,
            "images": images_data,
            "external_links": sorted(list(external)),
            "page_hash": page_hash,
            "md_filename": md_filename,
        }
        index_entry = (slug, title)
        return (visible_text, external_links, index_entry, md_filename, page_data)
    except RequestException as e:
        logger.error(f"HTTP error for {url}: {e}")
        return "", set(), ("", ""), "", {}
    except (OSError, AttributeError, ValueError) as e:  # pragma: no cover - unexpected
        logger.exception(f"Unexpected error processing {url}: {e}")
        raise PageProcessingError(str(e)) from e


def crawl_site(
    domain: str,
    base_url: str,
    folder: Path,
    visited_df: pd.DataFrame,
    max_pages: int,
    max_workers: int = 5,
    site_language: str = "english",
    timeout: int = HTTP_TIMEOUT,
    use_playwright: bool = False,
) -> Tuple[str, List[Dict]]:
    """
    Crawl site URLs concurrently and collect results.

    Iterates over URLs with status=2, processes each, updates visited log,
    exports external URLs, and returns concatenated text corpus and
    list of page_data dicts.

    :param use_playwright: force fetching pages via Playwright

    :Example:
        text_corpus, pages_data = crawl_site(
            'example-com', 'https://example.com', Path('example-com'), visited_df, 100, max_workers=5, site_language='en', timeout=HTTP_TIMEOUT
        )
    """
    if crawl_delay > 1.0:
        logger.info(
            f"Using high crawl_delay of {crawl_delay}s, crawling will be slower."
        )
    urls_to_visit = visited_df[visited_df["Status"] == 2]["URL"].tolist()[:max_pages]
    external_links: Set[str] = set()
    text_corpus: List[str] = []
    pages_data: List[dict] = []
    failed_urls: List[str] = []
    from tribeca_insights.playwright_crawler import fetch_with_playwright

    fetcher = (
        fetch_with_playwright if (use_playwright or len(urls_to_visit) > 3) else None
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(
                fetch_and_process,
                url,
                domain,
                folder,
                site_language,
                timeout,
                fetcher,
            ): url
            for url in urls_to_visit
        }
        for future in tqdm(
            concurrent.futures.as_completed(future_to_url), total=len(urls_to_visit)
        ):
            url = future_to_url[future]
            try:
                result = future.result()
                assert (
                    isinstance(result, tuple) and len(result) == 5
                ), f"Unexpected result format: {result}"
                visible_text, ext_links, index_entry, md_filename, page_data = result
                if visible_text:
                    text_corpus.append(visible_text)
                external_links.update(ext_links)
                visited_df.loc[visited_df["URL"] == url, "Status"] = 1
                visited_df["Data"] = visited_df["Data"].astype(str)
                visited_df.loc[visited_df["URL"] == url, "Data"] = (
                    datetime.now().strftime("%Y-%m-%d")
                )
                if md_filename:
                    visited_df["MD File"] = visited_df["MD File"].astype(str)
                    visited_df.loc[visited_df["URL"] == url, "MD File"] = md_filename
                if page_data:
                    pages_data.append(page_data)
            except PageProcessingError as e:
                logger.warning(f"Error processing {url}: {e}")
                failed_urls.append(url)
            except AssertionError as e:
                logger.error(f"Malformed result for {url}: {e}")
                failed_urls.append(url)
    if failed_urls:
        logger.info(f"Failed to process {len(failed_urls)} URLs: {failed_urls}")
    # Ensure the output directory exists before saving
    folder.mkdir(parents=True, exist_ok=True)
    save_visited_urls(visited_df, folder / f"visited_urls_{domain}.csv")
    export_external_urls(folder, external_links)
    return (" ".join(text_corpus), pages_data)
