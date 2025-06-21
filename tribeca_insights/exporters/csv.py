"""
Export CSV utilities for Tribeca Insights.

- update_keyword_frequency: update and save keyword frequency CSV.
- export_external_urls: export collected external URLs to a Markdown file.
"""

import logging
from pathlib import Path
from collections import Counter
from typing import Set

import pandas as pd

from tribeca_insights.text_utils import clean_and_tokenize

def update_keyword_frequency(folder: Path, domain: str, full_text: str, language: str='english') -> None:
    """Update and export keyword frequency CSV."""
    tokens = clean_and_tokenize(full_text, language)
    freq = Counter(tokens)
    csv_path = folder / f'keyword_frequency_{domain}.csv'
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        combined = Counter(dict(zip(existing['word'], existing['freq'])))
        combined.update(freq)
        freq = combined
    df = pd.DataFrame(freq.items(), columns=['word', 'freq']).sort_values(by='freq', ascending=False)
    df.to_csv(csv_path, index=False)
    logging.info(f'📊 Frequency exported: {csv_path}')

def export_external_urls(folder: Path, external_links: Set[str]) -> None:
    """Export external URLs to markdown file."""
    with open(folder / 'external_urls.md', 'w', encoding='utf-8') as f:
        f.write('# Collected External URLs\n\n')
        for link in sorted(external_links):
            f.write(f'- {link}\n')