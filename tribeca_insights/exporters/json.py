"""
Export JSON utilities for Tribeca Insights.

Provides functions to export page JSON, index JSON, external URLs JSON,
keyword frequency JSON, and visited URLs JSON.
"""

import json
import logging
from pathlib import Path

import pandas as pd
from typing import List, Set, Dict

logger = logging.getLogger(__name__)

JSON_PAGES_DIR = "pages_json"
JSON_INDEX = "index.json"
JSON_EXTERNAL = "external_urls.json"
JSON_FREQ_TEMPLATE = "keyword_frequency_{}.json"
JSON_DUMP_KWARGS = {"ensure_ascii": False, "indent": 2}

def export_pages_json(folder: Path, pages_data: List[Dict]) -> None:
    """
    Export each page data as individual JSON files in pages_json/ directory.

    Example:
        export_pages_json(Path("./output"), pages_data)

    Args:
        folder (Path): The folder to export JSON files into.
        pages_data (List[Dict]): List of page data dictionaries.

    Returns:
        None
    """
    folder.mkdir(parents=True, exist_ok=True)
    pages_json_dir = folder / JSON_PAGES_DIR
    pages_json_dir.mkdir(exist_ok=True, parents=True)
    for p in pages_data:
        slug = p.get("slug", p.get("md_filename", "").rstrip(".md"))
        path = pages_json_dir / f"{slug}.json"
        try:
            with open(path, "w", encoding="utf-8") as jf:
                json.dump(p, jf, **JSON_DUMP_KWARGS)
        except Exception as e:
            logger.error(f"Failed to write page JSON for slug '{slug}': {e}")
    logger.info(f"Exported {len(pages_data)} pages to JSON in {pages_json_dir}")
    return None

def export_index_json(folder: Path, pages_data: List[Dict]) -> None:
    """
    Generate index.json with a list of {slug, title, md_filename} for each page.

    Example:
        export_index_json(Path("./output"), pages_data)

    Args:
        folder (Path): The folder to export index.json into.
        pages_data (List[Dict]): List of page data dictionaries.

    Returns:
        None
    """
    folder.mkdir(parents=True, exist_ok=True)
    index = [
        {"slug": p["slug"], "title": p.get("title", ""), "md_filename": p.get("md_filename", "")}
        for p in pages_data
    ]
    index_path = folder / JSON_INDEX
    try:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, **JSON_DUMP_KWARGS)
    except Exception as e:
        logger.error(f"Failed to write index JSON to {index_path}: {e}")
    else:
        logger.info(f"Exported index for {len(index)} pages to {index_path}")
    return None

def export_external_urls_json(folder: Path, external_links: Set[str]) -> None:
    """
    Generate external_urls.json containing a list of external URLs.

    Example:
        export_external_urls_json(Path("./output"), external_links)

    Args:
        folder (Path): The folder to export external_urls.json into.
        external_links (Set[str]): Set of external URLs.

    Returns:
        None
    """
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / JSON_EXTERNAL
    urls_list = sorted(list(external_links))
    if not urls_list:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f, **JSON_DUMP_KWARGS)
        except Exception as e:
            logger.error(f"Failed to write external URLs JSON to {path}: {e}")
        else:
            logger.info("No external URLs to export")
        return None
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(urls_list, f, **JSON_DUMP_KWARGS)
    except Exception as e:
        logger.error(f"Failed to write external URLs JSON to {path}: {e}")
    else:
        logger.info(f"Exported {len(urls_list)} external URLs to {path}")
    return None

def export_keyword_frequency_json(folder: Path, domain: str) -> None:
    """
    Read keyword_frequency_<domain>.csv and generate keyword_frequency_<domain>.json with {word: freq}.

    Example:
        export_keyword_frequency_json(Path("./output"), "example.com")

    Args:
        folder (Path): The folder containing the CSV and to export JSON into.
        domain (str): The domain name used in the filename.

    Returns:
        None
    """
    csv_path = folder / f"keyword_frequency_{domain}.csv"
    json_path = folder / JSON_FREQ_TEMPLATE.format(domain)
    if not csv_path.exists():
        logger.warning(f"keyword_frequency CSV not found: {csv_path}")
        return None
    try:
        df = pd.read_csv(csv_path)
        freq: Dict[str, int] = dict(zip(df['word'], df['freq']))
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(freq, f, **JSON_DUMP_KWARGS)
    except Exception as e:
        logger.error(f"Failed to export keyword frequency JSON for domain '{domain}': {e}")
    else:
        logger.info(f"Exported keyword frequency JSON with {len(freq)} items to: {json_path}")
    return None

def export_visited_urls_json(visited_csv: Path) -> None:
    """
    Generate visited_urls_<domain>.json alongside the visited CSV file.

    Example:
        export_visited_urls_json(Path("./output/visited_urls_example.com.csv"))

    Args:
        visited_csv (Path): Path to the visited URLs CSV file.

    Returns:
        None
    """
    if not visited_csv.exists():
        logger.warning(f"visited_urls CSV not found: {visited_csv}")
        return None
    json_path = visited_csv.with_suffix('.json')
    json_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df = pd.read_csv(visited_csv)
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to export visited URLs JSON for {visited_csv}: {e}")
    else:
        logger.info(f"Exported visited URLs JSON with {len(df)} records to: {json_path}")
    return None