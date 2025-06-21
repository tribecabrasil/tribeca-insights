import os
import re
import logging
from pathlib import Path

def fetch_and_process(url: str, domain: str, folder: Path, language: str='english') -> Tuple[str, Set[str], Tuple[str, str], str, dict]:
    """
    Fetch a URL, export markdown, and return:
        - visible text,
        - external links,
        - index entry tuple (slug, title),
        - markdown filename,
        - page_data (dict with all metrics for JSON export)
    """
    try:
        logging.info(f'🔗 Visitando: {url}')
        resp = session.get(url, timeout=10)
        time.sleep(crawl_delay)
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        external_links: Set[str] = set()
        slug = slugify(urlparse(url).path or 'home')
        md_filename = f'{slug}.md'
        export_page_to_markdown(folder, url, html, domain, external_links)
        visible_text = extract_visible_text(html)
        try:
            title_tag = soup.title
            title = safe_strip(title_tag.string) if title_tag else '(sem título)'
        except Exception as e:
            logging.warning(f'[TITLE ERROR - FETCH] {url}: {e}')
            title = '(erro ao extrair título)'
        index_entry = (slug, title)
        try:
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            desc_content = desc_tag.get('content') if desc_tag else None
            description = safe_strip(desc_content)
        except Exception as e:
            logging.warning(f'[META DESCRIPTION ERROR - FETCH] {url}: {e}')
            description = '(erro ao extrair descrição)'
        headings = [tag.get_text(strip=True) for tag in soup.find_all(re.compile('^h[1-6]$'))]
        tokens = clean_and_tokenize(visible_text, language)
        local_freq = Counter(tokens)
        word_freq = dict(local_freq)
        images = soup.find_all('img')
        images_data = []
        for img in images:
            src = img.get('src', '–')
            alt = safe_strip(img.get('alt')) or ''
            images_data.append({'src': src, 'alt': alt})
        external = get_external_links(soup, domain)
        external_links.update(external)
        page_hash = hashlib.sha256(visible_text.encode('utf-8')).hexdigest()
        page_data = {'url': url, 'slug': slug, 'title': title, 'meta_description': description, 'headings': headings, 'word_count': len(tokens), 'word_frequency': word_freq, 'images': images_data, 'external_links': sorted(list(external)), 'page_hash': page_hash, 'md_filename': md_filename}
        return (visible_text, external_links, index_entry, md_filename, page_data)
    except Exception as e:
        logging.warning(f'⚠️ Erro em {url}: {e}')
        return ('', set(), None, None, None)

def crawl_site(domain: str, base_url: str, folder: Path, visited_df: pd.DataFrame, max_pages: int, max_workers: int, language: str='english') -> Tuple[str, list]:
    """
    Crawl site URLs concurrently, update visited_df, and return:
        - combined text corpus (for keyword frequency)
        - list of page_data dicts (for JSON export)
    """
    urls_to_visit = visited_df[visited_df['Status'] == 2]['URL'].tolist()[:max_pages]
    external_links: Set[str] = set()
    text_corpus: List[str] = []
    pages_data: List[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_and_process, url, domain, folder, language): url for url in urls_to_visit}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                visible_text, ext_links, index_entry, md_filename, page_data = future.result()
                if visible_text:
                    text_corpus.append(visible_text)
                external_links.update(ext_links)
                visited_df.loc[visited_df['URL'] == url, 'Status'] = 1
                visited_df.loc[visited_df['URL'] == url, 'Data'] = datetime.now().strftime('%Y-%m-%d')
                if md_filename:
                    visited_df.loc[visited_df['URL'] == url, 'MD File'] = md_filename
                if page_data:
                    pages_data.append(page_data)
            except Exception as e:
                logging.warning(f'⚠️ Erro processando {url}: {e}')
    save_visited_urls(visited_df, folder / f'visited_urls_{domain}.csv')
    export_external_urls(folder, external_links)
    return (' '.join(text_corpus), pages_data)