import os
import re
import logging
from pathlib import Path

def update_keyword_frequency(folder: Path, domain: str, full_text: str, language: str='english') -> None:
    """Update and export keyword frequency CSV."""
    tokens = clean_and_tokenize(full_text, language)
    freq = Counter(tokens)
    csv_path = folder / f'keyword_frequency_{domain}.csv'
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        combined = Counter(dict(zip(existing['Word'], existing['Frequency'])))
        combined.update(freq)
        freq = combined
    df = pd.DataFrame(freq.items(), columns=['Word', 'Frequency']).sort_values(by='Frequency', ascending=False)
    df.to_csv(csv_path, index=False)
    logging.info(f'📊 Frequência exportada: {csv_path}')

def export_external_urls(folder: Path, external_links: Set[str]) -> None:
    """Export external URLs to markdown file."""
    with open(folder / 'external_urls.md', 'w', encoding='utf-8') as f:
        f.write('# URLs Externas Coletadas\n\n')
        for link in sorted(external_links):
            f.write(f'- {link}\n')