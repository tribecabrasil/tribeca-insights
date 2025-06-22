"""
Export JSON utilities for Tribeca Insights.

Provides functions to export page JSON, index JSON, external URLs JSON,
keyword frequency JSON, and visited URLs JSON.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd

logger = logging.getLogger(__name__)

JSON_PAGES_DIR = "pages_json"
JSON_INDEX = "index.json"
JSON_EXTERNAL = "external_urls.json"
JSON_FREQ_TEMPLATE = "keyword_frequency_{}.json"
JSON_DUMP_KWARGS = {"ensure_ascii": False, "indent": 2}


def export_pages_json(folder: Path, pages_data: List[Dict]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    pages_json_dir = folder / JSON_PAGES_DIR
    pages_json_dir.mkdir(exist_ok=True, parents=True)
    for p in pages_data:
        slug = p.get("slug", p.get("md_filename", "").rstrip(".md"))
        path = pages_json_dir / f"{slug}.json"
        try:
            with open(path, "w", encoding="utf-8") as jf:
                json.dump(p, jf, **JSON_DUMP_KWARGS)
        except OSError as e:
            logger.error(f"Failed to write page JSON for slug '{slug}': {e}")
    logger.info(f"Exported {len(pages_data)} pages to JSON in {pages_json_dir}")
    return None


def export_index_json(folder: Path, pages_data: List[Dict]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    index = [
        {
            "slug": p["slug"],
            "title": p.get("title", ""),
            "md_filename": p.get("md_filename", ""),
        }
        for p in pages_data
    ]
    index_path = folder / JSON_INDEX
    try:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, **JSON_DUMP_KWARGS)
    except OSError as e:
        logger.error(f"Failed to write index JSON to {index_path}: {e}")
    else:
        logger.info(f"Exported index for {len(index)} pages to {index_path}")
    return None


def export_external_urls_json(folder: Path, external_links: Set[str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / JSON_EXTERNAL
    urls_list = sorted(list(external_links))
    if not urls_list:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f, **JSON_DUMP_KWARGS)
        except OSError as e:
            logger.error(f"Failed to write external URLs JSON to {path}: {e}")
        else:
            logger.info("No external URLs to export")
        return None
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(urls_list, f, **JSON_DUMP_KWARGS)
    except OSError as e:
        logger.error(f"Failed to write external URLs JSON to {path}: {e}")
    else:
        logger.info(f"Exported {len(urls_list)} external URLs to {path}")
    return None


def export_keyword_frequency_json(folder: Path, domain: str) -> None:
    csv_path = folder / f"keyword_frequency_{domain}.csv"
    json_path = folder / JSON_FREQ_TEMPLATE.format(domain)
    if not csv_path.exists():
        logger.warning(f"keyword_frequency CSV not found: {csv_path}")
        return None
    try:
        df = pd.read_csv(csv_path)
        freq: Dict[str, int] = dict(zip(df["word"], df["freq"]))
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(freq, f, **JSON_DUMP_KWARGS)
    except (pd.errors.ParserError, OSError) as e:
        logger.error(
            f"Failed to export keyword frequency JSON for domain '{domain}': {e}"
        )
    else:
        logger.info(
            f"Exported keyword frequency JSON with {len(freq)} items to: {json_path}"
        )
    return None


def export_visited_urls_json(visited_csv: Path) -> None:
    if not visited_csv.exists():
        logger.warning(f"visited_urls CSV not found: {visited_csv}")
        return None
    json_path = visited_csv.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df = pd.read_csv(visited_csv)
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    except (pd.errors.ParserError, OSError) as e:
        logger.error(f"Failed to export visited URLs JSON for {visited_csv}: {e}")
    else:
        logger.info(
            f"Exported visited URLs JSON with {len(df)} records to: {json_path}"
        )
    return None


def export_json(input_dir: str, out_file: str) -> None:
    """
    Combine all JSON page files from a directory into a single file.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {input_dir}")

    combined = []
    for json_file in input_path.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                combined.append(data)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to read {json_file}: {e}")

    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(combined, f, **JSON_DUMP_KWARGS)
    except OSError as e:
        logger.error(f"Failed to write combined JSON to {out_file}: {e}")
    else:
        logger.info(f"✅ Exported combined JSON to {out_file}")


def update_project_json(
    folder: Path,
    slug: str,
    base_url: str,
    language: str,
    pages_data: List[Dict],
    max_pages: int,
    workers: int,
    crawl_delay: float,
    crawler_engine: str = "BeautifulSoup",
) -> None:
    """Create or update the consolidated project metadata JSON.

    Args:
        folder: Output folder for the project JSON.
        slug: Project slug.
        base_url: Base URL for crawling.
        language: Site language.
        pages_data: List of page metadata dictionaries.
        max_pages: Maximum number of pages crawled.
        workers: Thread worker count.
        crawl_delay: Delay between HTTP requests.
        crawler_engine: Engine used for crawling.
    """

    from datetime import datetime

    from tribeca_insights.config import CRAWLED_BY, VERSION

    folder.mkdir(parents=True, exist_ok=True)
    project_path = folder / f"project_{slug}.json"
    now_iso = datetime.now().isoformat()
    if project_path.exists():
        try:
            with open(project_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (
            OSError,
            json.JSONDecodeError,
        ) as e:  # pragma: no cover - log error only
            logger.error(f"Failed to read existing project JSON: {e}")
            data = {}
    else:
        data = {}

    created_at = data.get("created_at", now_iso)

    pages_map = {p.get("slug"): p for p in data.get("pages", []) if p.get("slug")}
    for p in pages_data:
        slug_key = p.get("slug")
        if slug_key:
            pages_map[slug_key] = p

    data.update(
        {
            "version": VERSION,
            "crawled_by": CRAWLED_BY,
            "crawler_engine": crawler_engine,
            "project_slug": slug,
            "domain": slug,
            "base_url": base_url,
            "site_language": language,
            "language": language,
            "created_at": created_at,
            "last_updated_at": now_iso,
            "max_pages": max_pages,
            "max_workers": workers,
            "crawl_delay": crawl_delay,
            "pages": list(pages_map.values()),
            "pages_count": len(pages_map),
        }
    )

    try:
        with open(project_path, "w", encoding="utf-8") as f:
            json.dump(data, f, **JSON_DUMP_KWARGS)
    except OSError as e:  # pragma: no cover - log error only
        logger.error(f"Failed to write project JSON {project_path}: {e}")
    else:
        logger.info(f"Updated project JSON at {project_path}")
    return None
