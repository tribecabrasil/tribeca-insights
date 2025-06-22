"""
Export Markdown reports for Tribeca Insights.

Provides functions to export individual page analyses and generate an index of reports.

:Example:
    export_page_to_markdown(Path('example'), 'https://example.com', '<html>', 'example.com', set())
    export_index_markdown(Path('example'))
"""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from slugify import slugify

from tribeca_insights.text_utils import (
    clean_and_tokenize,
    extract_visible_text,
    safe_strip,
)

logger = logging.getLogger(__name__)

MD_PAGES_DIR = "pages_md"
MD_PAGES_PLAYWRIGHT_DIR = "pages_md_playwright"
INDEX_FILENAME = "index.md"


def export_page_to_markdown(
    folder: Path,
    url: str,
    html: str,
    domain: str,
    external_links: Set[str],
    subdirectory: str = MD_PAGES_DIR,
) -> None:
    """
    Export page content to a Markdown file.

    :param folder: project folder Path
    :param url: page URL
    :param html: raw HTML content
    :param domain: domain slug for URL parsing
    :param external_links: set to collect external links
    :param subdirectory: relative subfolder for Markdown pages
    """
    soup = BeautifulSoup(html, "html.parser")
    try:
        title_tag = soup.title
        title = safe_strip(title_tag.string) if title_tag else "(no title)"
    except (AttributeError, TypeError) as e:
        logger.warning(f"[TITLE ERROR] {url}: {e}")
        title = "(error extracting title)"
    try:
        desc_tag = soup.find("meta", attrs={"name": "description"})
        desc_content = desc_tag.get("content") if desc_tag else None
        description = safe_strip(desc_content)
    except (AttributeError, TypeError) as e:
        logger.warning(f"[META DESCRIPTION ERROR] {url}: {e}")
        description = "(error extracting description)"
    headings = [
        f"{'#' * int(tag.name[1])} {tag.get_text(strip=True)}"
        for tag in soup.find_all(re.compile(r"^h[1-6]$"))
    ]
    visible_text = extract_visible_text(html)
    tokens = clean_and_tokenize(visible_text)
    local_freq = Counter(tokens)
    images = soup.find_all("img")
    image_lines = []
    for img in images:
        src = img.get("src", "–")
        alt = safe_strip(img.get("alt")) or "_(no ALT)_"
        image_lines.append(f"- `src`: {src}\n  - alt: {alt}")
    from tribeca_insights.crawler import get_external_links

    external = get_external_links(soup, domain)
    external_links.update(external)
    slug = slugify(urlparse(url).path or "home")
    pages_dir = folder / subdirectory
    pages_dir.mkdir(parents=True, exist_ok=True)
    filepath = pages_dir / f"{slug}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# `{url}`\n\n")
        f.write(f"**Title**: {title}\n\n")
        f.write(f"**Meta Description**: {description}\n\n")

        f.write("## Headings\n")
        f.write(
            "\n".join(f"- {h}" for h in headings)
            if headings
            else "_No headings found._"
        )
        f.write("\n\n")

        f.write("## Word Frequency (Top 50)\n")
        for word, freq in local_freq.most_common(50):
            f.write(f"- **{word}**: {freq}\n")
        f.write("\n")

        f.write("## External Links\n")
        f.write(
            "\n".join(f"- {link}" for link in external)
            if external
            else "_No external links found._"
        )
        f.write("\n\n")

        f.write("## Images with ALT\n")
        f.write("\n".join(image_lines) if image_lines else "_No images found._\n")
        f.write("\n")

        f.write("## Cleaned Text\n")
        f.write(f"```\n{visible_text[:3000]}...\n```\n\n")

        f.write("## Raw HTML\n")
        f.write("```html\n")
        f.write(html[:5000])
        f.write("\n... (truncated)\n```\n\n")

        f.write("---\n")
        f.write(f"_Total words analyzed: {len(tokens)}_\n")
    logger.info(f"Exported Markdown for {url} to {filepath}")
    return None


def export_index_markdown(
    folder: Path, subdirectories: list[str] | None = None
) -> None:
    """Generate Markdown index of analyzed pages.

    :param folder: base project folder containing Markdown directories
    :param subdirectories: list of subfolders to index
    """
    if subdirectories is None:
        subdirectories = [MD_PAGES_DIR]
    index_path = folder / INDEX_FILENAME
    pages: list[Path] = []
    for sub in subdirectories:
        pages_dir = folder / sub
        pages_dir.mkdir(parents=True, exist_ok=True)
        pages.extend(sorted(pages_dir.glob("*.md")))
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Analyzed Pages Index\n\n")
        for page in pages:
            title = page.stem.replace("-", " ").title()
            rel_path = page.relative_to(folder)
            f.write(f"- [{title}]({rel_path})\n")
    logger.info(f"Exported index Markdown to {index_path}")
    return None


def export_markdown(input_dir: Path | str, out_dir: Path | str) -> None:
    """
    Unified Markdown export interface.
    Currently, this function simply generates the index for Markdown reports.

    :param input_dir: Path to the domain folder
    :param out_dir: Path to write pages_md and index.md
    """
    input_dir = Path(input_dir)
    out_dir = Path(out_dir)
    export_index_markdown(out_dir, [MD_PAGES_DIR, MD_PAGES_PLAYWRIGHT_DIR])


__all__ = ["export_page_to_markdown", "export_index_markdown", "export_markdown"]
