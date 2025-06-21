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

logger = logging.getLogger(__name__)

# Filename templates
CSV_FILENAME_TEMPLATE = "keyword_frequency_{}.csv"
MD_FILENAME = "external_urls.md"
MD_HEADER = "# Collected External URLs\n\n"

def update_keyword_frequency(folder: Path, domain: str, full_text: str, language: str = "english") -> None:
    """
    Update and save keyword frequency CSV for a domain.

    :param folder: output directory Path
    :param domain: slug of the domain
    :param full_text: concatenated text from all pages
    :param language: language code for tokenization (e.g., "english")
    :return: None
    :Example:
        update_keyword_frequency(Path('example'), 'example-com', 'hello world', 'english')
    """
    folder.mkdir(parents=True, exist_ok=True)
    tokens: list[str] = clean_and_tokenize(full_text, language)
    freq: Counter = Counter(tokens)
    csv_path = folder / CSV_FILENAME_TEMPLATE.format(domain)
    existing_df = pd.DataFrame()
    if csv_path.exists():
        try:
            existing_df = pd.read_csv(csv_path)
            combined = Counter(dict(zip(existing_df['word'], existing_df['freq'])))
            combined.update(freq)
            freq = combined
        except Exception as e:
            logger.warning(f"Could not read existing CSV {csv_path}: {e}")
    df = pd.DataFrame(freq.items(), columns=['word', 'freq']).sort_values(by='freq', ascending=False)
    try:
        df.to_csv(csv_path, index=False)
        logger.info(f"Exported {len(df)} keyword frequencies to {csv_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV {csv_path}: {e}")
    return None

def export_external_urls(folder: Path, external_links: Set[str]) -> None:
    """
    Export external URLs to a Markdown file.

    :param folder: output directory Path
    :param external_links: set of external URL strings
    :return: None
    :Example:
        export_external_urls(Path('example'), {'https://example.com'})
    """
    folder.mkdir(parents=True, exist_ok=True)
    md_path = folder / MD_FILENAME
    try:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(MD_HEADER)
            if not external_links:
                f.write('_No external URLs found._\n')
            else:
                for link in sorted(external_links):
                    f.write(f'- {link}\n')
        logger.info(f"Exported {len(external_links)} external URLs to {md_path}")
    except Exception as e:
        logger.error(f"Failed to write Markdown {md_path}: {e}")
    return None