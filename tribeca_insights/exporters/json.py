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

def export_pages_json(folder: Path, pages_data: List[Dict]) -> None:
    """
    Export each page data as individual JSON files in pages_json/ directory.
    """
    pages_json_dir = folder / "pages_json"
    pages_json_dir.mkdir(exist_ok=True, parents=True)
    for p in pages_data:
        slug = p.get("slug", p.get("md_filename", "").rstrip(".md"))
        path = pages_json_dir / f"{slug}.json"
        with open(path, "w", encoding="utf-8") as jf:
            json.dump(p, jf, ensure_ascii=False, indent=2)
    logging.info(f"Exported pages JSON to: {pages_json_dir}")

def export_index_json(folder: Path, pages_data: List[Dict]) -> None:
    """
    Generate index.json with a list of {slug, title, md_filename} for each page.
    """
    index = [
        {"slug": p["slug"], "title": p.get("title", ""), "md_filename": p.get("md_filename", "")}
        for p in pages_data
    ]
    index_path = folder / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    logging.info(f"Exported index JSON to: {index_path}")

def export_external_urls_json(folder: Path, external_links: Set[str]) -> None:
    """
    Generate external_urls.json containing a list of external URLs.
    """
    path = folder / "external_urls.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(list(external_links)), f, ensure_ascii=False, indent=2)
    logging.info(f"Exported external URLs JSON to: {path}")

def export_keyword_frequency_json(folder: Path, domain: str) -> None:
    """
    Read keyword_frequency_<domain>.csv and generate keyword_frequency_<domain>.json with {word: freq}.
    """
    csv_path = folder / f"keyword_frequency_{domain}.csv"
    if not csv_path.exists():
        logging.warning(f"keyword_frequency CSV not found: {csv_path}")
        return
    df = pd.read_csv(csv_path)
    freq = dict(zip(df['word'], df['freq']))
    json_path = folder / f"keyword_frequency_{domain}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(freq, f, ensure_ascii=False, indent=2)
    logging.info(f"Exported keyword frequency JSON to: {json_path}")

def export_visited_urls_json(visited_csv: Path) -> None:
    """
    Generate visited_urls_<domain>.json alongside the visited CSV file.
    """
    if not visited_csv.exists():
        logging.warning(f"visited_urls CSV not found: {visited_csv}")
        return
    df = pd.read_csv(visited_csv)
    json_path = visited_csv.with_suffix('.json')
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    logging.info(f"Exported visited URLs JSON to: {json_path}")