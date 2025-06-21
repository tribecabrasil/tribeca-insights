"""
Core crawling logic for Tribeca Insights.

Defines functions to fetch and process pages concurrently, extract content,
and export results to Markdown/CSV.
"""

import hashlib
import logging
import time
import re
from pathlib import Path
import concurrent.futures
from collections import Counter
from typing import List, Set, Tuple, Dict
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from slugify import slugify

from urllib.parse import urlparse
from tribeca_insights.config import crawl_delay, session
from tribeca_insights.text_utils import safe_strip, extract_visible_text, clean_and_tokenize
from tribeca_insights.exporters.markdown import export_page_to_markdown
from tribeca_insights.storage import save_visited_urls
from tribeca_insights.exporters.csv import export_external_urls

def get_external_links(soup: BeautifulSoup, domain: str) -> Set[str]:
    """
    Extract external HTTP links not containing the domain.
    """
    return {
        a["href"] for a in soup.find_all("a", href=True)
        if a["href"].startswith("http") and domain not in a["href"]
    }

def fetch_and_process(url: str, domain: str, folder: Path, language: str='english') -> Tuple[str, Set[str], Tuple[str, str], str, Dict]:
    """
    Fetch and process a single page.

    Retrieves HTML, sleeps for crawl_delay, parses content, exports Markdown,
    and returns visible text, external links, index entry, markdown filename,
    and full page data for JSON export.

    :param url: URL to fetch
    :param domain: base domain slug
    :param folder: output folder Path
    :param language: language code for tokenization
    :return: tuple (visible_text, external_links, index_entry, md_filename, page_data)
    """
    try:
        logging.info(f'🔗 Visitando: {url}')
        resp = session.get(url, timeout=10)
        time.sleep(crawl_delay)
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        external_links: Set[str] = set()
        slug = slugify(urlparse(url).path or 'home')
        md_filename = f'{slug}.md'
        export_page_to_markdown(folder, url, html, domain, external_links)
        visible_text = extract_visible_text(html)
        try:
            title_tag = soup.title
            title = safe_strip(title_tag.string) if title_tag else '(sem título)'
        except Exception as e:
            logging.warning(f'[TITLE ERROR - FETCH] {url}: {e}')
            title = '(erro ao extrair título)'
        index_entry = (slug, title)
        try:
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            desc_content = desc_tag.get('content') if desc_tag else None
            description = safe_strip(desc_content)
        except Exception as e:
            logging.warning(f'[META DESCRIPTION ERROR - FETCH] {url}: {e}')
            description = '(erro ao extrair descrição)'
        headings = [tag.get_text(strip=True) for tag in soup.find_all(re.compile('^h[1-6]$'))]
        tokens = clean_and_tokenize(visible_text, language)
        local_freq = Counter(tokens)
        word_freq = dict(local_freq)
        images = soup.find_all('img')
        images_data = []
        for img in images:
            src = img.get('src', '–')
            alt = safe_strip(img.get('alt')) or ''
            images_data.append({'src': src, 'alt': alt})
        external = get_external_links(soup, domain)
        external_links.update(external)
        page_hash = hashlib.sha256(visible_text.encode('utf-8')).hexdigest()
        page_data = {'url': url, 'slug': slug, 'title': title, 'meta_description': description, 'headings': headings, 'word_count': len(tokens), 'word_frequency': word_freq, 'images': images_data, 'external_links': sorted(list(external)), 'page_hash': page_hash, 'md_filename': md_filename}
        return (visible_text, external_links, index_entry, md_filename, page_data)
    except Exception as e:
        logging.warning(f'⚠️ Erro em {url}: {e}')
        return ('', set(), None, None, None)

def crawl_site(domain: str, base_url: str, folder: Path, visited_df: pd.DataFrame, max_pages: int, max_workers: int, language: str='english') -> Tuple[str, List[Dict]]:
    """
    Crawl site URLs concurrently and collect results.

    Iterates over URLs with status=2, processes each, updates visited log,
    exports external URLs, and returns concatenated text corpus and
    list of page_data dicts.

    :param domain: domain slug
    :param base_url: full base URL
    :param folder: Path for outputs
    :param visited_df: DataFrame of visited URLs
    :param max_pages: max pages to crawl
    :param max_workers: number of threads
    :param language: language code
    :return: tuple (text_corpus, pages_data)
    """
    urls_to_visit = visited_df[visited_df['Status'] == 2]['URL'].tolist()[:max_pages]
    external_links: Set[str] = set()
    text_corpus: List[str] = []
    pages_data: List[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_and_process, url, domain, folder, language): url for url in urls_to_visit}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                visible_text, ext_links, index_entry, md_filename, page_data = future.result()
                if visible_text:
                    text_corpus.append(visible_text)
                external_links.update(ext_links)
                visited_df.loc[visited_df['URL'] == url, 'Status'] = 1
                visited_df.loc[visited_df['URL'] == url, 'Data'] = datetime.now().strftime('%Y-%m-%d')
                if md_filename:
                    visited_df.loc[visited_df['URL'] == url, 'MD File'] = md_filename
                if page_data:
                    pages_data.append(page_data)
            except Exception as e:
                logging.warning(f'⚠️ Erro processando {url}: {e}')
    save_visited_urls(visited_df, folder / f'visited_urls_{domain}.csv')
    export_external_urls(folder, external_links)
    return (' '.join(text_corpus), pages_data)