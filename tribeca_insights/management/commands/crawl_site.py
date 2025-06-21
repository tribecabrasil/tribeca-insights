# tribeca_insights/management/commands/crawl_site.py
from django.core.management.base import BaseCommand

from tribeca_insights.crawler import crawl_site


class Command(BaseCommand):
    help = "Crawl a website via Django"

    def add_arguments(self, parser):
        parser.add_argument(
            "domain", type=str, help="Target domain (e.g., example.com)"
        )
        parser.add_argument(
            "base_url",
            type=str,
            help="Base URL to start crawling (e.g., https://example.com)",
        )
        parser.add_argument(
            "--max-pages",
            type=int,
            default=100,
            help="Maximum number of pages to crawl",
        )
        parser.add_argument(
            "--language",
            type=str,
            default="en",
            help="Language for stopword filtering (e.g., en, pt-br)",
        )
        parser.add_argument(
            "--workers", type=int, default=4, help="Number of worker threads"
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=10,
            help="Timeout in seconds for each request",
        )

    def handle(self, *args, **options):
        crawl_site(
            domain=options["domain"],
            base_url=options["base_url"],
            max_pages=options["max_pages"],
            language=options["language"],
            workers=options["workers"],
            timeout=options["timeout"],
        )
