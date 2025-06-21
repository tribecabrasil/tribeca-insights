"""
Export Markdown reports for Tribeca Insights.

Provides functions to export individual page analyses and generate an index of reports.

:Example:
    export_page_to_markdown(Path('example'), 'https://example.com', '<html>', 'example.com', set())
    export_index_markdown(Path('example'))
"""

import re
import logging
from pathlib import Path
from collections import Counter
from typing import Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from slugify import slugify

from tribeca_insights.text_utils import safe_strip, extract_visible_text, clean_and_tokenize

logger = logging.getLogger(__name__)

MD_PAGES_DIR = "pages_md"
INDEX_FILENAME = "index.md"

def export_page_to_markdown(folder: Path, url: str, html: str, domain: str, external_links: Set[str]) -> None:
    """
    Export page content to a Markdown file.

    :param folder: project folder Path
    :param url: page URL
    :param html: raw HTML content
    :param domain: domain slug for URL parsing
    :param external_links: set to collect external links
    :return: None
    :Example:
        export_page_to_markdown(
            Path('example'), 'https://example.com', '<html>...</html>', 'example.com', set()
        )
    """
    soup = BeautifulSoup(html, 'html.parser')
    try:
        title_tag = soup.title
        title = safe_strip(title_tag.string) if title_tag else '(no title)'
    except Exception as e:
        logger.warning(f'[TITLE ERROR] {url}: {e}')
        title = '(error extracting title)'
    try:
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc_content = desc_tag.get('content') if desc_tag else None
        description = safe_strip(desc_content)
    except Exception as e:
        logger.warning(f'[META DESCRIPTION ERROR] {url}: {e}')
        description = '(error extracting description)'
    headings = [
        f"{'#' * int(tag.name[1])} {tag.get_text(strip=True)}"
        for tag in soup.find_all(re.compile(r'^h[1-6]$'))
    ]
    visible_text = extract_visible_text(html)
    tokens = clean_and_tokenize(visible_text)
    local_freq = Counter(tokens)
    images = soup.find_all('img')
    image_lines = []
    for img in images:
        src = img.get('src', '–')
        alt = safe_strip(img.get('alt')) or '_(no ALT)_'
        image_lines.append(f'- `src`: {src}\n  - alt: {alt}')
    from tribeca_insights.crawler import get_external_links
    external = get_external_links(soup, domain)
    external_links.update(external)
    slug = slugify(urlparse(url).path or 'home')
    pages_dir = folder / MD_PAGES_DIR
    pages_dir.mkdir(parents=True, exist_ok=True)
    filepath = pages_dir / f'{slug}.md'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'# Page Analysis: `{url}`\n\n')
        f.write(f'**Title:** {title}\n\n')
        f.write(f'**Meta Description:** {description}\n\n')
        f.write('## Headings Hierarchy\n')
        f.write('\n'.join(headings) if headings else '_No headings found._')
        f.write('\n\n')
        f.write('## Main Content (cleaned)\n')
        f.write(f'```\n{visible_text[:3000]}...\n```\n\n')
        f.write('## Word Frequency (top 20)\n')
        for word, freq in local_freq.most_common(20):
            f.write(f'- **{word}**: {freq}\n')
        f.write('\n## Images with ALT Texts\n')
        f.write('\n'.join(image_lines) if image_lines else '_No images found._\n')
        f.write('\n---\n')
        f.write(f'_Total words analyzed: {len(tokens)}_\n')
    logger.info(f"Exported Markdown for {url} to {filepath}")
    return None

def export_index_markdown(folder: Path) -> None:
    """Generate Markdown index of analyzed pages.

    :param folder: base project folder containing pages_md directory
    :return: None
    :Example:
        export_index_markdown(Path('example'))
    """
    pages_dir = folder / MD_PAGES_DIR
    index_path = folder / INDEX_FILENAME
    pages_dir.mkdir(parents=True, exist_ok=True)
    pages = sorted(pages_dir.glob('*.md'))
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('# Analyzed Pages Index\n\n')
        for page in pages:
            title = page.stem.replace('-', ' ').title()
            rel_path = page.relative_to(folder)
            f.write(f'- [{title}]({rel_path})\n')
    logger.info(f"Exported index Markdown to {index_path}")
    return None