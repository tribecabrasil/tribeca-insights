"""
Export functions for JSON artifacts in the crawling pipeline.

Provides:
- export_pages_json: individual page JSON files in pages_json directory.
- export_index_json: combined index.json of page metadata.
- export_external_urls_json: list of external URLs.
- export_keyword_frequency_json: JSON of word frequencies.
- export_visited_urls_json: mirror CSV of visited URLs in JSON.
"""

import json
import logging
from pathlib import Path

import pandas as pd

from tribeca_insights.exporters.json import JSON_DUMP_KWARGS

from typing import List, Set, Dict

logger = logging.getLogger(__name__)

# Output paths and filename patterns
PAGES_DIR = "pages_json"
INDEX_FILE = "index.json"
EXT_URLS_FILE = "external_urls.json"
FREQ_JSON_TEMPLATE = "keyword_frequency_{}.json"
VISITED_JSON_SUFFIX = ".json"


def export_pages_json(folder: Path, pages_data: List[Dict]) -> None:
    """
    Export each page data as individual JSON files.

    :param folder: base project folder path
    :param pages_data: list of page metadata dicts
    :return: None
    :Example:
        export_pages_json(Path('example'), pages_data)
    """
    pages_json_dir = folder / PAGES_DIR
    pages_json_dir.mkdir(parents=True, exist_ok=True)
    try:
        for p in pages_data:
            slug = p.get("slug") or p.get("md_filename", "").rstrip(".md") or "unknown"
            with open(pages_json_dir / f"{slug}.json", "w", encoding="utf-8") as jf:
                json.dump(p, jf, **JSON_DUMP_KWARGS)
    except Exception as e:
        logger.error(f"Failed to export pages JSON to {pages_json_dir}: {e}")
    else:
        logger.info(f"Exported {len(pages_data)} page JSON files to {pages_json_dir}")
    return None


def export_index_json(folder: Path, pages_data: List[Dict]) -> None:
    """
    Generate index.json with list of {slug, title, md_filename} for each page.

    :param folder: base project folder path
    :param pages_data: list of page metadata dicts
    :return: None
    :Example:
        export_index_json(Path('example'), pages_data)
    """
    index = [
        {"slug": p["slug"], "title": p.get("title", ""), "md_filename": p.get("md_filename", "")}
        for p in pages_data
    ]
    index_path = folder / INDEX_FILE
    try:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to export index JSON to {index_path}: {e}")
    else:
        logger.info(f"Exported index JSON with {len(index)} entries to {index_path}")
    return None


def export_external_urls_json(folder: Path, external_links: Set[str]) -> None:
    """
    Generate external_urls.json containing list of external URLs.

    :param folder: base project folder path
    :param external_links: set of external URLs
    :return: None
    :Example:
        export_external_urls_json(Path('example'), external_links)
    """
    ext_urls_path = folder / EXT_URLS_FILE
    try:
        with open(ext_urls_path, "w", encoding="utf-8") as f:
            json.dump(sorted(list(external_links)), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to export external URLs JSON to {ext_urls_path}: {e}")
    else:
        logger.info(f"Exported {len(external_links)} external URLs to {ext_urls_path}")
    return None


def export_keyword_frequency_json(folder: Path, domain: str) -> None:
    """
    Read keyword_frequency_<domain>.csv and generate keyword_frequency_<domain>.json with {word: freq}.

    :param folder: base project folder path
    :param domain: domain name to locate CSV and name JSON
    :return: None
    :Example:
        export_keyword_frequency_json(Path('example'), 'mydomain')
    """
    csv_path = folder / f"keyword_frequency_{domain}.csv"
    json_path = folder / FREQ_JSON_TEMPLATE.format(domain)
    try:
        df = pd.read_csv(csv_path)
        freq = dict(zip(df['word'], df['freq']))
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(freq, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to export keyword frequency JSON for domain '{domain}' from {csv_path}: {e}")
    else:
        logger.info(f"Exported keyword frequency JSON for domain '{domain}' with {len(freq)} entries to {json_path}")
    return None


def export_visited_urls_json(visited_csv: Path) -> None:
    """
    Generate visited_urls_<domain>.json alongside the CSV of visits.

    :param visited_csv: path to the CSV file of visited URLs
    :return: None
    :Example:
        export_visited_urls_json(Path('example/visited_urls_mydomain.csv'))
    """
    json_path = visited_csv.with_suffix(VISITED_JSON_SUFFIX)
    try:
        visited_csv.parent.mkdir(parents=True, exist_ok=True)
        df = pd.read_csv(visited_csv)
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to export visited URLs JSON from {visited_csv} to {json_path}: {e}")
    else:
        logger.info(f"Exported visited URLs JSON with {len(df)} records to {json_path}")
    return None