#!/usr/bin/env python3
"""
CLI entrypoint for Tribeca Insights.
"""
import argparse
import importlib.metadata
import logging
from pathlib import Path

import pandas as pd

from tribeca_insights.config import HTTP_TIMEOUT, SUPPORTED_LANGUAGES
from tribeca_insights.crawler import crawl_site
from tribeca_insights.storage import (
    add_urls_from_sitemap,
    load_visited_urls,
    reconcile_md_files,
    save_visited_urls,
    setup_project_folder,
)
from tribeca_insights.text_utils import setup_environment

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main entrypoint: parse CLI args, set up environment, run crawl and exports.
    """
    parser = argparse.ArgumentParser(description="Tribeca Insights CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=importlib.metadata.version("tribeca-insights"),
        help="Show program version and exit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    # add subcommands
    subparsers = parser.add_subparsers(dest="command", required=True)

    # crawl subcommand
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a site")
    crawl_parser.add_argument(
        "--max-pages", type=int, default=50, help="Maximum number of pages to crawl"
    )
    crawl_parser.add_argument(
        "--language",
        choices=SUPPORTED_LANGUAGES,
        default="en",
        help="Language code for stopwords",
    )
    crawl_parser.add_argument(
        "--workers", type=int, default=5, help="Number of worker threads for crawling"
    )
    crawl_parser.add_argument(
        "--timeout",
        type=int,
        default=HTTP_TIMEOUT,
        help="HTTP request timeout in seconds",
    )
    crawl_parser.add_argument(
        "--slug", type=str, required=True, help="Site slug (e.g. 'next-health.com')"
    )
    crawl_parser.add_argument(
        "--base-url",
        type=str,
        required=True,
        help="Base URL to start crawling (e.g. 'https://www.next-health.com')",
    )

    # export subcommand
    export_parser = subparsers.add_parser("export", help="Export the latest crawl data")
    export_parser.add_argument(
        "--slug", type=str, required=True, help="Site slug identifier for export"
    )
    export_parser.add_argument(
        "--format",
        choices=["csv", "json", "markdown"],
        default="csv",
        help="Export format: csv, json, or markdown",
    )

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    setup_environment()

    if args.command == "crawl":
        cmd_args = args
        slug = cmd_args.slug
        base_url = cmd_args.base_url
        language = cmd_args.language
        project_folder = setup_project_folder(slug)
        visited_df = load_visited_urls(Path.cwd(), slug)
        if visited_df.empty:
            logger.info(f"Seeding initial URL '{base_url}' for crawl queue")
            visited_df = pd.DataFrame(
                [{"URL": base_url, "Status": 2, "Data": "", "MD File": ""}]
            )
            save_visited_urls(visited_df, Path.cwd() / f"visited_urls_{slug}.csv")

        visited_df = reconcile_md_files(visited_df, project_folder)
        visited_df = add_urls_from_sitemap(base_url, visited_df)
        save_visited_urls(visited_df, Path.cwd() / f"visited_urls_{slug}.csv")
        crawl_site(
            slug,
            base_url,
            project_folder,
            visited_df,
            cmd_args.max_pages,
            cmd_args.workers,
            site_language=language,
            timeout=cmd_args.timeout,
        )
    elif args.command == "export":
        from tribeca_insights.exporters import export_data  # implement export_data()

        export_data(args.slug, args.format)

    logger.info("Analysis completed.")
    return None


if __name__ == "__main__":
    main()