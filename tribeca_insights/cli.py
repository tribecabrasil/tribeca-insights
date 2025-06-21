"""
CLI Interface for Tribeca Insights.

Handles user interaction: domain selection (existing or new), URL entry, and site language choice.
"""
import logging
import re
import ssl
from pathlib import Path
from typing import List, Tuple, NamedTuple
from urllib.parse import urlparse
import nltk
from tribeca_insights.config import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

class DomainConfig(NamedTuple):
    slug: str
    base_url: str
    language: str

def setup_environment() -> None:
    """
    Configure SSL to accept unverified HTTPS and ensure NLTK stopwords are available.

    :raises AttributeError: if SSL context override is not supported.
    """
    try:
        _create_unverified_https_context = ssl._create_unverified_context
        ssl._create_default_https_context = _create_unverified_https_context
    except AttributeError:
        pass
    nltk.download('stopwords', quiet=True)

def ask_for_domain(existing_csvs: List[str]) -> DomainConfig:
    """
    Prompt the user to select an existing domain or enter a new URL, then choose the site language.

    :param existing_csvs: list of paths to visited_urls CSV files
    :return: DomainConfig with slug, base_url, and language
    """
    valid_csvs = []
    for f in existing_csvs:
        basename = Path(f).name
        m = re.match(r'visited_urls_(.+)\.csv$', basename)
        if m and m.group(1).strip():
            valid_csvs.append(f)
    domain_map = {}
    print('\n📁 Domains already analyzed:')
    for idx, file in enumerate(valid_csvs, 1):
        domain = re.match(r'visited_urls_(.+)\.csv$', Path(file).name).group(1)
        domain_map[str(idx)] = domain
        print(f'{idx}. {domain}')
    print(f'{len(domain_map) + 1}. 🔗 Enter new URL')
    choice = input('\nChoose an option (number): ').strip()
    if choice in domain_map:
        domain = domain_map[choice]
        base_url = f'https://{domain}'
    else:
        while True:
            base_url = input('\n🌐 Enter the new URL (e.g., https://www.tribecadigital.com.br): ').strip()
            try:
                parsed = urlparse(base_url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError(f"Invalid URL entered: {base_url}")
                break
            except ValueError as e:
                print(f"❌ {e} Please try again.")
        domain = parsed.netloc.replace('www.', '')
    # Prompt for site language by number
    print("\n🌐 Supported site languages:")
    for idx, lang in enumerate(SUPPORTED_LANGUAGES, start=1):
        print(f"{idx}. {lang}")
    # Default to English (1)
    while True:
        choice = input("Choose language number [1]: ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(SUPPORTED_LANGUAGES):
            site_language = SUPPORTED_LANGUAGES[int(choice) - 1]
            break
        print(f"❌ Invalid choice. Enter a number between 1 and {len(SUPPORTED_LANGUAGES)}.")
    return DomainConfig(slug=domain, base_url=base_url, language=site_language)