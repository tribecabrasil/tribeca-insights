import os
import re
import logging
from pathlib import Path

def export_page_to_markdown(folder: Path, url: str, html: str, domain: str, external_links: Set[str]) -> None:
    """Export page content to markdown file."""
    soup = BeautifulSoup(html, 'html.parser')
    try:
        title_tag = soup.title
        title = safe_strip(title_tag.string) if title_tag else '(sem título)'
    except Exception as e:
        logging.warning(f'[TITLE ERROR] {url}: {e}')
        title = '(erro ao extrair título)'
    try:
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc_content = desc_tag.get('content') if desc_tag else None
        description = safe_strip(desc_content)
    except Exception as e:
        logging.warning(f'[META DESCRIPTION ERROR] {url}: {e}')
        description = '(erro ao extrair descrição)'
    headings = [f'{'#' * int(tag.name[1])} {tag.get_text(strip=True)}' for tag in soup.find_all(re.compile('^h[1-6]$'))]
    visible_text = extract_visible_text(html)
    tokens = clean_and_tokenize(visible_text)
    local_freq = Counter(tokens)
    images = soup.find_all('img')
    image_lines = []
    for img in images:
        src = img.get('src', '–')
        alt = safe_strip(img.get('alt')) or '_(sem ALT)_'
        image_lines.append(f'- `src`: {src}\n  - alt: {alt}')
    external = get_external_links(soup, domain)
    external_links.update(external)
    slug = slugify(urlparse(url).path or 'home')
    filepath = folder / 'pages_md' / f'{slug}.md'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'# Análise de Página: `{url}`\n\n')
        f.write(f'**Título:** {title}\n\n')
        f.write(f'**Meta Description:** {description}\n\n')
        f.write('## Hierarquia de Headings\n')
        f.write('\n'.join(headings) if headings else '_Nenhum heading encontrado._')
        f.write('\n\n')
        f.write('## Conteúdo Principal (limpo)\n')
        f.write(f'```\n{visible_text[:3000]}...\n```\n\n')
        f.write('## Frequência de Palavras (top 20)\n')
        for word, freq in local_freq.most_common(20):
            f.write(f'- **{word}**: {freq}\n')
        f.write('\n## Imagens com ALT texts\n')
        f.write('\n'.join(image_lines) if image_lines else '_Nenhuma imagem encontrada._\n')
        f.write('\n---\n')
        f.write(f'_Total de palavras analisadas: {len(tokens)}_\n')

def gerar_indice_markdown(folder: Path) -> None:
    """Generate markdown index file with links to analyzed pages."""
    index_path = folder / 'index.md'
    pages = sorted((folder / 'pages_md').glob('*.md'))
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('# Índice de Páginas Analisadas\n\n')
        for page in pages:
            title = page.stem.replace('-', ' ').title()
            rel_path = page.relative_to(folder)
            f.write(f'- [{title}]({rel_path})\n')