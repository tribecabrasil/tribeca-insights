import os
import re
import logging
from pathlib import Path

def load_visited_urls(csv_path: Path) -> pd.DataFrame:
    """Load visited URLs CSV or create empty DataFrame."""
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=['URL', 'Status', 'Data'])
    if 'MD File' not in df.columns:
        df['MD File'] = ''
    return df

def save_visited_urls(df: pd.DataFrame, csv_path: Path) -> None:
    """Save visited URLs DataFrame to CSV removing duplicates."""
    df = df.drop_duplicates(subset=['URL'])
    df.to_csv(csv_path, index=False)

def add_urls_from_sitemap(base_url: str, visited_df: pd.DataFrame) -> pd.DataFrame:
    """Add URLs from sitemap.xml to visited DataFrame."""
    sitemap_url = urljoin(base_url, '/sitemap.xml')
    try:
        resp = session.get(sitemap_url, timeout=10)
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
                new_df = pd.DataFrame(new_rows)
                return pd.concat([visited_df, new_df], ignore_index=True)
    except Exception as e:
        logging.warning(f'⚠️ Erro ao acessar sitemap.xml: {e}')
    return visited_df

def reconcile_md_files(visited_df: pd.DataFrame, folder: Path) -> pd.DataFrame:
    """
    Para cada URL com Status 1 e MD File vazio, verifica se o arquivo .md existe em pages_md.
    - Se existir, preenche `MD File` com o nome do arquivo.
    - Se não existir, redefine Status para 2 para reprocessamento.
    """
    for idx, row in visited_df.iterrows():
        if row['Status'] == 1 and (not row['MD File']):
            slug = slugify(urlparse(row['URL']).path or 'home')
            md_path = folder / 'pages_md' / f'{slug}.md'
            if md_path.exists():
                visited_df.at[idx, 'MD File'] = f'{slug}.md'
            else:
                visited_df.at[idx, 'Status'] = 2
    return visited_df