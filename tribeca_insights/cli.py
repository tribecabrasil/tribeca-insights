"""
CLI Interface for Tribeca Insights.

Handles user interaction: domain selection (existing or new), URL entry, and site language choice.
"""
import os
import re
import ssl
from urllib.parse import urlparse
from typing import List, Tuple
import nltk
from tribeca_insights.config import SUPPORTED_LANGUAGES

def setup_environment() -> None:
    """
    Configure SSL context for unverified HTTPS and download NLTK stopwords.
    """
    try:
        _create_unverified_https_context = ssl._create_unverified_context
        ssl._create_default_https_context = _create_unverified_https_context
    except AttributeError:
        pass
    nltk.download('stopwords', quiet=True)

def ask_for_domain(existing_csvs: List[str]) -> Tuple[str, str, str]:
    """
    Prompt the user to select an existing domain or enter a new URL, then choose the site language.

    :param existing_csvs: list of paths to visited_urls CSV files
    :return: tuple of (domain_slug, base_url, site_language)
    """
    valid_csvs = []
    for f in existing_csvs:
        basename = os.path.basename(f)
        m = re.match(r'visited_urls_(.+)\.csv$', basename)
        if m and m.group(1).strip():
            valid_csvs.append(f)
    domain_map = {}
    print('\n📁 Domains already analyzed:')
    for idx, file in enumerate(valid_csvs, 1):
        domain = re.match(r'visited_urls_(.+)\.csv$', os.path.basename(file)).group(1)
        domain_map[str(idx)] = domain
        print(f'{idx}. {domain}')
    print(f'{len(domain_map) + 1}. 🔗 Enter new URL')
    choice = input('\nChoose an option (number): ').strip()
    if choice in domain_map:
        domain = domain_map[choice]
        base_url = f'https://{domain}'
    else:
        base_url = input('\n🌐 Enter the new URL (e.g., https://www.tribecadigital.com.br): ').strip()
        domain = urlparse(base_url).netloc.replace('www.', '')
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
    return (domain, base_url, site_language)