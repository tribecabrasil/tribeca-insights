"""
Export Markdown reports for Tribeca Insights.

Provides functions to export individual page analyses and generate an index of reports.
"""

import logging
import re
from pathlib import Path
from collections import Counter
from typing import Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from slugify import slugify

from tribeca_insights.text_utils import safe_strip, extract_visible_text, clean_and_tokenize
from tribeca_insights.crawler import get_external_links

def export_page_to_markdown(folder: Path, url: str, html: str, domain: str, external_links: Set[str]) -> None:
    """Export page content to markdown file."""
    soup = BeautifulSoup(html, 'html.parser')
    try:
        title_tag = soup.title
        title = safe_strip(title_tag.string) if title_tag else '(sem título)'
    except Exception as e:
        logging.warning(f'[TITLE ERROR] {url}: {e}')
        title = '(erro ao extrair título)'
    try:
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc_content = desc_tag.get('content') if desc_tag else None
        description = safe_strip(desc_content)
    except Exception as e:
        logging.warning(f'[META DESCRIPTION ERROR] {url}: {e}')
        description = '(erro ao extrair descrição)'
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
        alt = safe_strip(img.get('alt')) or '_(sem ALT)_'
        image_lines.append(f'- `src`: {src}\n  - alt: {alt}')
    external = get_external_links(soup, domain)
    external_links.update(external)
    slug = slugify(urlparse(url).path or 'home')
    filepath = folder / 'pages_md' / f'{slug}.md'
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

def gerar_indice_markdown(folder: Path) -> None:
    """Generate markdown index file with links to analyzed pages."""
    index_path = folder / 'index.md'
    pages = sorted((folder / 'pages_md').glob('*.md'))
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('# Índice de Páginas Analisadas\n\n')
        for page in pages:
            title = page.stem.replace('-', ' ').title()
            rel_path = page.relative_to(folder)
            f.write(f'- [{title}]({rel_path})\n')