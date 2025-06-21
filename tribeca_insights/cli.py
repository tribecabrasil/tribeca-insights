import os
import re
import logging
from pathlib import Path

def setup_environment() -> None:
    """Setup SSL context and download NLTK stopwords."""
    try:
        _create_unverified_https_context = ssl._create_unverified_context
        ssl._create_default_https_context = _create_unverified_https_context
    except AttributeError:
        pass
    nltk.download('stopwords', quiet=True)

def ask_for_domain(existing_csvs: List[str]) -> Tuple[str, str]:
    """Ask user to select existing domain or input new URL. Also prompt for site language."""
    valid_csvs = []
    for f in existing_csvs:
        basename = os.path.basename(f)
        m = re.match('visited_urls_(.+)\\.csv$', basename)
        if m and m.group(1).strip():
            valid_csvs.append(f)
    domain_map = {}
    print('\n📁 Domínios já analisados:')
    for idx, file in enumerate(valid_csvs, 1):
        domain = re.match('visited_urls_(.+)\\.csv$', os.path.basename(file)).group(1)
        domain_map[str(idx)] = domain
        print(f'{idx}. {domain}')
    print(f'{len(domain_map) + 1}. 🔗 Digitar nova URL')
    choice = input('\nEscolha uma opção (número): ').strip()
    if choice in domain_map:
        domain = domain_map[choice]
        base_url = f'https://{domain}'
    else:
        base_url = input('\n🌐 Digite a nova URL (ex: https://www.next-health.com): ').strip()
        domain = urlparse(base_url).netloc.replace('www.', '')
    print('\n🌐 Qual o idioma principal do site? (en / pt-br)')
    site_language = input('site_language [en]: ').strip().lower()
    if not site_language:
        site_language = 'en'
    return (domain, base_url, site_language)