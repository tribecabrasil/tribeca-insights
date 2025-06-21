"""
Export CSV utilities for Tribeca Insights.

- update_keyword_frequency: update and save keyword frequency CSV.
- export_external_urls: export collected external URLs to a Markdown file.
"""

import logging
from collections import Counter
from pathlib import Path
from typing import Set

import pandas as pd

from tribeca_insights.exporters.constants import (
    CSV_FILENAME_TEMPLATE,
    MD_FILENAME,
    MD_HEADER,
)
from tribeca_insights.text_utils import clean_and_tokenize

logger = logging.getLogger(__name__)

# (removidas — agora importadas de constants)


def update_keyword_frequency(
    folder: Path, domain: str, full_text: str, language: str = "english"
) -> None:
    """
    Update and save keyword frequency CSV for a domain.

    :param folder: output directory Path
    :param domain: slug of the domain
    :param full_text: concatenated text from all pages
    :param language: language code for tokenization (e.g., "english")
    :return: None
    """
    folder.mkdir(parents=True, exist_ok=True)
    tokens: list[str] = clean_and_tokenize(full_text, language)
    freq: Counter[str] = Counter(tokens)
    csv_path: Path = folder / CSV_FILENAME_TEMPLATE.format(domain)
    if csv_path.exists():
        logger.info(f"Overwriting existing keyword frequency file: {csv_path}")
    if freq:
        df: pd.DataFrame = pd.DataFrame(
            freq.items(), columns=["word", "freq"]
        ).sort_values(by="freq", ascending=False)
    else:
        df = pd.DataFrame(columns=["word", "freq"])
    try:
        df.to_csv(csv_path, index=False)
        logger.info(f"Exported {len(df)} keyword frequencies to {csv_path}")
        logger.info(f"Keyword frequency CSV exported to: {csv_path}")
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
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(MD_HEADER)
            if not external_links:
                f.write("_No external URLs found._\n")
            else:
                for link in sorted(external_links):
                    f.write(f"- {link}\n")
        logger.info(f"Exported {len(external_links)} external URLs to {md_path}")
    except Exception as e:
        logger.error(f"Failed to write Markdown {md_path}: {e}")
    return None


def export_csv(input_dir: str, out_file: str) -> None:
    """
    Export combined keyword frequency CSV from a directory of JSON page files.

    :param input_dir: directory containing page JSON files
    :param out_file: output CSV file path
    """
    import json
    from pathlib import Path

    all_text = []
    for fname in Path(input_dir).glob("*.json"):
        try:
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_text.append(data.get("text", ""))
        except Exception as e:
            logger.warning(f"Error reading {fname}: {e}")
    full_text = "\n".join(all_text)
    update_keyword_frequency(Path(out_file).parent, Path(out_file).stem, full_text)
