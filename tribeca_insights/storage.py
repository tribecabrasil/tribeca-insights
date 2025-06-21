"""
Storage utilities for Tribeca Insights.

Manages the visited URLs log and extracts URLs from sitemaps.
"""

import logging
from pathlib import Path
from typing import List

import pandas as pd
import xml.etree.ElementTree as ET
from slugify import slugify
from urllib.parse import urljoin, urlparse
from requests.exceptions import RequestException

from tribeca_insights.config import session
from tribeca_insights.config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)

def load_visited_urls(base_path: Path, domain: str) -> pd.DataFrame:
    """
    Load the visited URLs CSV for the given domain inside base_path.
    Returns an empty DataFrame if the file does not exist or cannot be read.
    """
    csv_name = f"visited_urls_{domain}.csv"
    csv_path = base_path / csv_name
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} visited URLs from {csv_path}")
        except Exception as e:
            logger.warning(f"Could not read visited URLs CSV {csv_path}: {e}")
            df = pd.DataFrame(columns=['URL', 'Status', 'Data', 'MD File'])
    else:
        logger.info(f"No existing visited URLs file found at {csv_path}, starting fresh.")
        df = pd.DataFrame(columns=['URL', 'Status', 'Data', 'MD File'])
    return df

def save_visited_urls(df: pd.DataFrame, csv_path: Path) -> None:
    """Save visited URLs DataFrame to CSV removing duplicates."""
    df = df.drop_duplicates(subset=['URL'])
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved {len(df)} visited URLs to {csv_path}")

def add_urls_from_sitemap(base_url: str, visited_df: pd.DataFrame) -> pd.DataFrame:
    """Add URLs from sitemap.xml to visited DataFrame."""
    sitemap_url = urljoin(base_url, '/sitemap.xml')
    try:
        resp = session.get(sitemap_url, timeout=HTTP_TIMEOUT)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            new_rows = []
            for url in root.findall('.//ns:loc', ns):
                if not url.text:
                    continue
                loc = url.text.strip()
                if loc not in visited_df['URL'].values:
                    new_rows.append({'URL': loc, 'Status': 2, 'Data': ''})
            if new_rows:
                logger.info(f"Added {len(new_rows)} new URLs from sitemap")
                new_df = pd.DataFrame(new_rows)
                return pd.concat([visited_df, new_df], ignore_index=True)
    except ET.ParseError as e:
        logger.warning(f"Error parsing sitemap XML at {sitemap_url}: {e}")
        return visited_df
    except RequestException as e:
        logger.warning(f'Error accessing sitemap.xml at {sitemap_url}: {e}')
    return visited_df

def reconcile_md_files(visited_df: pd.DataFrame, folder: Path) -> pd.DataFrame:
    """
    For each URL with status 1 and an empty MD File field,
    checks if the corresponding Markdown file exists in pages_md.
    - If the file exists, fills 'MD File' with the filename.
    - Otherwise, resets status to 2 for reprocessing.
    """
    for idx, row in visited_df.iterrows():
        if row['Status'] == 1 and (not row['MD File']):
            slug = slugify(urlparse(row['URL']).path or 'home')
            md_path = folder / 'pages_md' / f'{slug}.md'
            # If the markdown file exists, update 'MD File' with filename
            if md_path.exists():
                visited_df.at[idx, 'MD File'] = f'{slug}.md'
            else:
                # If not, reset status to 2 for reprocessing
                visited_df.at[idx, 'Status'] = 2
    return visited_df