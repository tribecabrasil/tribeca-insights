# -*- coding: utf-8 -*-
# Módulo de exportação JSON para SEO Crawler

import os
import re
import logging
from pathlib import Path

import json
import pandas as pd
from typing import List, Set, Dict

def export_pages_json(folder: Path, pages_data: List[Dict]) -> None:
    """
    Para cada dicionário de page_data, grava um JSON em pages_json/<slug>.json.
    """
    pages_json_dir = folder / "pages_json"
    pages_json_dir.mkdir(exist_ok=True, parents=True)
    for p in pages_data:
        slug = p.get("slug", p.get("md_filename", "").rstrip(".md"))
        path = pages_json_dir / f"{slug}.json"
        with open(path, "w", encoding="utf-8") as jf:
            json.dump(p, jf, ensure_ascii=False, indent=2)

def export_index_json(folder: Path, pages_data: List[Dict]) -> None:
    """
    Gera index.json com lista de {slug, title, md_filename} para cada página.
    """
    index = [
        {"slug": p["slug"], "title": p.get("title", ""), "md_filename": p.get("md_filename", "")}
        for p in pages_data
    ]
    with open(folder / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

def export_external_urls_json(folder: Path, external_links: Set[str]) -> None:
    """
    Gera external_urls.json contendo lista de URLs externas.
    """
    path = folder / "external_urls.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(list(external_links)), f, ensure_ascii=False, indent=2)

def export_keyword_frequency_json(folder: Path, domain: str) -> None:
    """
    Lê keyword_frequency_<domain>.csv e gera keyword_frequency_<domain>.json com {word: freq}.
    """
    csv_path = folder / f"keyword_frequency_{domain}.csv"
    if not csv_path.exists():
        logging.warning(f"keyword_frequency CSV não encontrado: {csv_path}")
        return
    df = pd.read_csv(csv_path)
    freq = dict(zip(df['word'], df['freq']))
    with open(folder / f"keyword_frequency_{domain}.json", "w", encoding="utf-8") as f:
        json.dump(freq, f, ensure_ascii=False, indent=2)

def export_visited_urls_json(visited_csv: Path) -> None:
    """
    Gera visited_urls_<domain>.json paralelo ao CSV de visitas.
    """
    if not visited_csv.exists():
        logging.warning(f"visited_urls CSV não encontrado: {visited_csv}")
        return
    df = pd.read_csv(visited_csv)
    json_path = visited_csv.with_suffix('.json')
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)