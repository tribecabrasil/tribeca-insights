#!/usr/bin/env python3
"""
CLI entrypoint for Tribeca Insights.
"""
import argparse
import logging
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from slugify import slugify

from tribeca_insights.config import SUPPORTED_LANGUAGES, HTTP_TIMEOUT
from tribeca_insights.storage import load_visited_urls, save_visited_urls
from tribeca_insights.crawler import crawl_site
from tribeca_insights.text_utils import setup_environment

logger = logging.getLogger(__name__)

def ask_for_domain(existing_csvs: list[Path]) -> tuple[str, str, str]:
    """
    Prompt user to select an existing domain or enter a new URL,
    then choose the site language.

    :param existing_csvs: list of Paths to visited_urls CSV files
    :return: tuple (slug, base_url, language)
    """
    # List existing
    print("\n📁 Domains already analyzed:")
    for idx, path in enumerate(existing_csvs, start=1):
        slug = path.stem.replace("visited_urls_", "")
        print(f"{idx}. {slug}")
    print(f"{len(existing_csvs)+1}. Enter new URL")

    choice = input("\nChoose an option (number): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(existing_csvs):
        slug = existing_csvs[int(choice)-1].stem.replace("visited_urls_", "")
        base_url = f"https://{slug}"
    else:
        while True:
            base_url = input("Enter the new URL: ").strip()
            parsed = urlparse(base_url)
            if parsed.scheme and parsed.netloc:
                slug = parsed.netloc.replace("www.", "")
                break
            print("Invalid URL, please try again.")

    # Language selection
    print("\nSupported site languages:")
    for idx, lang in enumerate(SUPPORTED_LANGUAGES, start=1):
        print(f"{idx}. {lang}")
    choice = input("Choose language number [1]: ").strip() or "1"
    language = SUPPORTED_LANGUAGES[int(choice)-1]

    return slug, base_url, language

def main() -> None:
    """
    Main entrypoint: parse CLI args, set up environment, run crawl and exports.
    """
    parser = argparse.ArgumentParser(description="Tribeca Insights CLI")
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--language", choices=SUPPORTED_LANGUAGES, default="en")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=HTTP_TIMEOUT)
    parser.add_argument("--domain", type=str, default=None)
    args = parser.parse_args()

    setup_environment()

    if args.domain:
        slug = urlparse(args.domain).netloc.replace("www.", "")
        base_url = args.domain
        language = args.language
    else:
        existing = list(Path.cwd().glob("visited_urls_*.csv"))
        slug, base_url, language = ask_for_domain(existing)

    # Load or initialize visited URLs history
    visited_df = load_visited_urls(Path.cwd(), slug)

    # Seed the home page on first run if no history exists
    if visited_df.empty:
        logger.info(f"Seeding initial URL '{base_url}' for crawl queue")
        visited_df = pd.DataFrame([{
            'URL': base_url,
            'Status': 2,
            'Data': '',
            'MD File': ''
        }])
        # Persist the seeded history
        save_visited_urls(visited_df, Path.cwd() / f"visited_urls_{slug}.csv")

    text_corpus, pages_data = crawl_site(
        slug, base_url, Path(slug),
        visited_df, args.max_pages,
        args.workers, site_language=language,
        timeout=args.timeout
    )

    logger.info("Analysis completed.")
    return None

if __name__ == "__main__":
    main()