"""
CLI entrypoint for Tribeca Insights.

Orchestrates argument parsing, environment setup, crawling, and export.
"""

import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import ssl
import time
import urllib.robotparser as robotparser
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple
from urllib.error import URLError
from urllib.parse import urljoin, urlparse

import nltk
import pandas as pd
import requests
from bs4 import BeautifulSoup
from slugify import slugify

crawl_delay = 0.0

logger = logging.getLogger(__name__)

crawl_delay = 0.0


def get_crawl_delay(base_url: str) -> float:
    """Fetch crawl-delay from robots.txt or return 0."""
    parser = robotparser.RobotFileParser()
    parser.set_url(urljoin(base_url, "/robots.txt"))
    try:
        parser.read()
        delay = parser.crawl_delay("SeoCrawler")
        if delay is None:
            delay = parser.crawl_delay("*")
        return delay or 0.0
    except Exception:
        return 0.0


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# Helper function to strip whitespace or return an empty string, logging when None
def safe_strip(value):
    if value is None:
        logger.debug("safe_strip recebeu None")
        return ""
    return value.strip() if isinstance(value, str) else ""


VERSION = "1.0"
USER_AGENT = f"SeoCrawler/{VERSION}"
CRAWLED_BY = USER_AGENT
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


# Configure the environment to allow NLTK downloads and avoid SSL errors on some platforms
def setup_environment() -> None:
    """Setup SSL context and download NLTK stopwords."""
    try:
        _create_unverified_https_context = ssl._create_unverified_context
        ssl._create_default_https_context = _create_unverified_https_context
    except AttributeError:
        pass
    nltk.download("stopwords", quiet=True)


# Clean and tokenize text by removing non-letter characters, collapsing spaces and stopwords.
# This helper centralizes text processing for frequency analysis to avoid duplication.
def clean_and_tokenize(text: str, language: str = "english") -> List[str]:
    """Clean and tokenize text removing stopwords and short words."""
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    tokens = text.lower().split()
    stop_words = set(nltk.corpus.stopwords.words(language))
    return [word for word in tokens if word not in stop_words and len(word) > 2]


# Extract visible text from HTML, removing tags that do not contribute to the main content
def extract_visible_text(html: str) -> str:
    """Extract visible text from HTML excluding non-content tags."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "svg", "footer", "nav", "meta"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return text.strip() if text else ""


# Get all internal links for the domain from the HTML content
def get_internal_links(soup: BeautifulSoup, base_url: str, domain: str) -> Set[str]:
    """Get internal links from soup belonging to the domain."""
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("/") or domain in href:
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc.replace("www.", "") == domain:
                links.add(full_url.split("#")[0])
    return links


# Get external links from the HTML that do not belong to the domain
def get_external_links(soup: BeautifulSoup, domain: str) -> Set[str]:
    """Get external links from soup not belonging to the domain."""
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("http") and domain not in href:
            links.add(href)
    return links


# Load the visited URLs CSV file or create an empty DataFrame if it doesn't exist
def load_visited_urls(csv_path: Path) -> pd.DataFrame:
    """Load visited URLs CSV or create empty DataFrame."""
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=["URL", "Status", "Data"])
    if "MD File" not in df.columns:
        df["MD File"] = ""
    return df


# Save the visited URLs DataFrame to CSV, removing duplicates to maintain integrity
def save_visited_urls(df: pd.DataFrame, csv_path: Path) -> None:
    """Save visited URLs DataFrame to CSV removing duplicates."""
    df = df.drop_duplicates(subset=["URL"])
    df.to_csv(csv_path, index=False)


# Prompt the user to choose an existing domain or enter a new URL to start crawling
def ask_for_domain(existing_csvs: List[str]) -> Tuple[str, str]:
    """Ask user to select existing domain or input new URL. Also prompt for site language."""
    # Filter out any CSVs with empty domain (e.g., visited_urls_.csv)
    valid_csvs = []
    for f in existing_csvs:
        basename = os.path.basename(f)
        # match visited_urls_<non-empty>.csv
        m = re.match(r"visited_urls_(.+)\.csv$", basename)
        if m and m.group(1).strip():
            valid_csvs.append(f)
    domain_map = {}
    print("\n📁 Domínios já analisados:")
    for idx, file in enumerate(valid_csvs, 1):
        domain = re.match(r"visited_urls_(.+)\.csv$", os.path.basename(file)).group(1)
        domain_map[str(idx)] = domain
        print(f"{idx}. {domain}")
    print(f"{len(domain_map) + 1}. 🔗 Digitar nova URL")

    choice = input("\nEscolha uma opção (número): ").strip()
    if choice in domain_map:
        domain = domain_map[choice]
        base_url = f"https://{domain}"
    else:
        base_url = input(
            "\n🌐 Digite a nova URL (ex: https://www.next-health.com): "
        ).strip()
        domain = urlparse(base_url).netloc.replace("www.", "")
    # Prompt for language
    print("\n🌐 Qual o idioma principal do site? (en / pt-br)")
    site_language = input("site_language [en]: ").strip().lower()
    if not site_language:
        site_language = "en"
    return domain, base_url, site_language


# Create the folder structure used to store the analysis artifacts
def setup_project_folder(domain: str) -> Path:
    """Create project folder and pages_md subfolder."""
    folder = Path(slugify(domain))
    folder.mkdir(exist_ok=True)
    (folder / "pages_md").mkdir(exist_ok=True)
    return folder


# Query the domain's sitemap.xml to add new URLs to the visited DataFrame
def add_urls_from_sitemap(base_url: str, visited_df: pd.DataFrame) -> pd.DataFrame:
    """Add URLs from sitemap.xml to visited DataFrame."""
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    try:
        resp = session.get(sitemap_url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            new_rows = []
            for url in root.findall(".//ns:loc", ns):
                if not url.text:
                    continue
                loc = url.text.strip()
                if loc not in visited_df["URL"].values:
                    new_rows.append({"URL": loc, "Status": 2, "Data": ""})
            if new_rows:
                new_df = pd.DataFrame(new_rows)
                return pd.concat([visited_df, new_df], ignore_index=True)
    except Exception as e:
        logger.warning(f"Erro ao acessar sitemap.xml: {e}")
    return visited_df


# Export page content to a Markdown file including title, description, headings, text, frequency data and images
def export_page_to_markdown(
    folder: Path, url: str, html: str, domain: str, external_links: Set[str]
) -> None:
    """Export page content to markdown file."""
    soup = BeautifulSoup(html, "html.parser")
    # Safe extraction of title
    try:
        title_tag = soup.title
        title = safe_strip(title_tag.string) if title_tag else "(sem título)"
    except Exception as e:
        logger.warning(f"[TITLE ERROR] {url}: {e}")
        title = "(erro ao extrair título)"

    # Safe extraction of meta description
    try:
        desc_tag = soup.find("meta", attrs={"name": "description"})
        desc_content = desc_tag.get("content") if desc_tag else None
        description = safe_strip(desc_content)
    except Exception as e:
        logger.warning(f"[META DESCRIPTION ERROR] {url}: {e}")
        description = "(erro ao extrair descrição)"

    headings = [
        f"{'#' * int(tag.name[1])} {tag.get_text(strip=True)}"
        for tag in soup.find_all(re.compile("^h[1-6]$"))
    ]

    visible_text = extract_visible_text(html)
    tokens = clean_and_tokenize(visible_text)
    local_freq = Counter(tokens)

    images = soup.find_all("img")
    image_lines = []
    for img in images:
        src = img.get("src", "–")
        alt = safe_strip(img.get("alt")) or "_(sem ALT)_"
        image_lines.append(f"- `src`: {src}\n  - alt: {alt}")

    external = get_external_links(soup, domain)
    external_links.update(external)

    slug = slugify(urlparse(url).path or "home")
    filepath = folder / "pages_md" / f"{slug}.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Análise de Página: `{url}`\n\n")
        f.write(f"**Título:** {title}\n\n")
        f.write(f"**Meta Description:** {description}\n\n")
        f.write("## Hierarquia de Headings\n")
        f.write("\n".join(headings) if headings else "_Nenhum heading encontrado._")
        f.write("\n\n")
        f.write("## Conteúdo Principal (limpo)\n")
        f.write(f"```\n{visible_text[:3000]}...\n```\n\n")
        f.write("## Frequência de Palavras (top 20)\n")
        for word, freq in local_freq.most_common(20):
            f.write(f"- **{word}**: {freq}\n")
        f.write("\n## Imagens com ALT texts\n")
        f.write(
            "\n".join(image_lines) if image_lines else "_Nenhuma imagem encontrada._\n"
        )
        f.write("\n---\n")
        f.write(f"_Total de palavras analisadas: {len(tokens)}_\n")


def fetch_and_process(
    url: str, domain: str, folder: Path, language: str = "english"
) -> Tuple[str, Set[str], Tuple[str, str], str, dict]:
    """
    Fetch a URL, export markdown, and return:
        - visible text,
        - external links,
        - index entry tuple (slug, title),
        - markdown filename,
        - page_data (dict with all metrics for JSON export)
    """
    try:
        logger.info(f"Visitando: {url}")
        resp = session.get(url, timeout=10)
        time.sleep(crawl_delay)
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        external_links: Set[str] = set()

        # Determine the Markdown filename before exporting
        slug = slugify(urlparse(url).path or "home")
        md_filename = f"{slug}.md"

        export_page_to_markdown(folder, url, html, domain, external_links)
        visible_text = extract_visible_text(html)

        try:
            title_tag = soup.title
            title = safe_strip(title_tag.string) if title_tag else "(sem título)"
        except Exception as e:
            logger.warning(f"[TITLE ERROR - FETCH] {url}: {e}")
            title = "(erro ao extrair título)"
        index_entry = (slug, title)

        # Meta description
        try:
            desc_tag = soup.find("meta", attrs={"name": "description"})
            desc_content = desc_tag.get("content") if desc_tag else None
            description = safe_strip(desc_content)
        except Exception as e:
            logger.warning(f"[META DESCRIPTION ERROR - FETCH] {url}: {e}")
            description = "(erro ao extrair descrição)"

        # Headings
        headings = [
            tag.get_text(strip=True) for tag in soup.find_all(re.compile("^h[1-6]$"))
        ]

        # Word frequency
        tokens = clean_and_tokenize(visible_text, language)
        local_freq = Counter(tokens)
        word_freq = dict(local_freq)

        # Images with alt
        images = soup.find_all("img")
        images_data = []
        for img in images:
            src = img.get("src", "–")
            alt = safe_strip(img.get("alt")) or ""
            images_data.append({"src": src, "alt": alt})

        # External links
        external = get_external_links(soup, domain)
        external_links.update(external)

        # Hash for page content
        page_hash = hashlib.sha256(visible_text.encode("utf-8")).hexdigest()

        page_data = {
            "url": url,
            "slug": slug,
            "title": title,
            "meta_description": description,
            "headings": headings,
            "word_count": len(tokens),
            "word_frequency": word_freq,
            "images": images_data,
            "external_links": sorted(list(external)),
            "page_hash": page_hash,
            "md_filename": md_filename,
        }

        return visible_text, external_links, index_entry, md_filename, page_data
    except Exception as e:
        logger.warning(f"Erro em {url}: {e}")
        return "", set(), None, None, None


# Crawl pending URLs, update status, and collect text for analysis
def crawl_site(
    domain: str,
    base_url: str,
    folder: Path,
    visited_df: pd.DataFrame,
    max_pages: int,
    max_workers: int,
    language: str = "english",
) -> Tuple[str, list]:
    """
    Crawl site URLs concurrently, update visited_df, and return:
        - combined text corpus (for keyword frequency)
        - list of page_data dicts (for JSON export)
    """
    urls_to_visit = visited_df[visited_df["Status"] == 2]["URL"].tolist()[:max_pages]
    external_links: Set[str] = set()
    text_corpus: List[str] = []
    pages_data: List[dict] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(fetch_and_process, url, domain, folder, language): url
            for url in urls_to_visit
        }
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                visible_text, ext_links, index_entry, md_filename, page_data = (
                    future.result()
                )
                if visible_text:
                    text_corpus.append(visible_text)
                external_links.update(ext_links)

                visited_df.loc[visited_df["URL"] == url, "Status"] = 1
                visited_df.loc[visited_df["URL"] == url, "Data"] = (
                    datetime.now().strftime("%Y-%m-%d")
                )
                if md_filename:
                    visited_df.loc[visited_df["URL"] == url, "MD File"] = md_filename
                if page_data:
                    pages_data.append(page_data)
            except Exception as e:
                logger.warning(f"Erro processando {url}: {e}")

    save_visited_urls(visited_df, folder / f"visited_urls_{domain}.csv")
    export_external_urls(folder, external_links)
    return " ".join(text_corpus), pages_data


# Update and export keyword frequency to a CSV file, merging with any existing data
def update_keyword_frequency(
    folder: Path, domain: str, full_text: str, language: str = "english"
) -> None:
    """Update and export keyword frequency CSV."""
    tokens = clean_and_tokenize(full_text, language)
    freq = Counter(tokens)

    csv_path = folder / f"keyword_frequency_{domain}.csv"
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        combined = Counter(dict(zip(existing["Word"], existing["Frequency"])))
        combined.update(freq)
        freq = combined

    df = pd.DataFrame(freq.items(), columns=["Word", "Frequency"]).sort_values(
        by="Frequency", ascending=False
    )
    df.to_csv(csv_path, index=False)
    logger.info(f"Frequência exportada: {csv_path}")


# Export the external URLs found during crawling to a Markdown file
def export_external_urls(folder: Path, external_links: Set[str]) -> None:
    """Export external URLs to markdown file."""
    with open(folder / "external_urls.md", "w", encoding="utf-8") as f:
        f.write("# URLs Externas Coletadas\n\n")
        for link in sorted(external_links):
            f.write(f"- {link}\n")


# Reconcile missing MD File entries so pages can be reprocessed if needed
def reconcile_md_files(visited_df: pd.DataFrame, folder: Path) -> pd.DataFrame:
    """
    For each URL with status ``1`` and an empty ``MD File`` field, check whether
    the corresponding ``.md`` file exists in ``pages_md``.

    - If it exists, fill ``MD File`` with the filename.
    - Otherwise reset ``Status`` to ``2`` so the page will be reprocessed.
    """
    for idx, row in visited_df.iterrows():
        if row["Status"] == 1 and not row["MD File"]:
            slug = slugify(urlparse(row["URL"]).path or "home")
            md_path = folder / "pages_md" / f"{slug}.md"
            if md_path.exists():
                visited_df.at[idx, "MD File"] = f"{slug}.md"
            else:
                visited_df.at[idx, "Status"] = 2
    return visited_df


# Generate a Markdown index with links to all analyzed pages to aid navigation
def gerar_indice_markdown(folder: Path) -> None:
    """Generate markdown index file with links to analyzed pages."""
    index_path = folder / "index.md"
    pages = sorted((folder / "pages_md").glob("*.md"))
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Índice de Páginas Analisadas\n\n")
        for page in pages:
            title = page.stem.replace("-", " ").title()
            rel_path = page.relative_to(folder)
            f.write(f"- [{title}]({rel_path})\n")


# Main function orchestrating the full crawling and analysis workflow,
# including setup, history loading, crawling, keyword analysis and index generation.
def main() -> None:
    """
    Main entrypoint: parse CLI args, set up environment, run crawl workflow,
    and export Markdown, CSV, and JSON artifacts.
    """
    setup_environment()

    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--language", type=str, default=None)
    parser.add_argument("--max-workers", type=int, default=5)
    parser.add_argument("--delay", type=float, default=None)
    args = parser.parse_args()

    existing_csvs = list(Path.cwd().glob("visited_urls_*.csv"))
    domain, base_url, site_language = ask_for_domain(existing_csvs)
    folder = setup_project_folder(domain)

    # Prefer CLI language if provided
    language = (
        args.language
        if args.language
        else ("portuguese" if site_language.startswith("pt") else "english")
    )

    global crawl_delay
    crawl_delay = args.delay if args.delay is not None else get_crawl_delay(base_url)

    visited_csv = folder / f"visited_urls_{domain}.csv"
    visited_df = load_visited_urls(visited_csv)
    # Reconcile missing MD File entries to ensure reprocessing when needed
    visited_df = reconcile_md_files(visited_df, folder)
    visited_df = add_urls_from_sitemap(base_url, visited_df)

    save_visited_urls(visited_df, visited_csv)

    project_created_at = datetime.now().isoformat()
    full_text, pages_data = crawl_site(
        domain,
        base_url,
        folder,
        visited_df,
        max_pages=args.max_pages,
        max_workers=args.max_workers,
        language=language,
    )
    update_keyword_frequency(folder, domain, full_text, language=language)
    gerar_indice_markdown(folder)

    # Export full JSON with all metadata and pages (with merging/updating)
    project_slug = slugify(domain)
    project_json_path = folder / f"project_{project_slug}.json"

    # Prepare project metadata
    project_created_at = project_created_at  # original timestamp
    project_updated_at = datetime.now().isoformat()

    # If a project JSON already exists, load and merge
    if project_json_path.exists():
        with open(project_json_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        # Preserve original creation date
        existing_created = existing.get("created_at", project_created_at)
        # Update metadata
        existing.update(
            {
                "version": VERSION,
                "crawled_by": CRAWLED_BY,
                "domain": domain,
                "base_url": base_url,
                "site_language": site_language,
                "language": language,
                "last_updated_at": project_updated_at,
                "max_pages": args.max_pages,
                "max_workers": args.max_workers,
                "crawl_delay": crawl_delay,
            }
        )
        # Merge pages: replace or add by slug
        pages_map = {p["slug"]: p for p in existing.get("pages", [])}
        for p in pages_data:
            pages_map[p["slug"]] = p
        existing["pages"] = list(pages_map.values())
        existing["pages_count"] = len(existing["pages"])
        project_data = existing
    else:
        # New project data
        project_data = {
            "version": VERSION,
            "crawled_by": CRAWLED_BY,
            "project_slug": project_slug,
            "domain": domain,
            "base_url": base_url,
            "site_language": site_language,
            "language": language,
            "created_at": project_created_at,
            "last_updated_at": project_created_at,
            "max_pages": args.max_pages,
            "max_workers": args.max_workers,
            "crawl_delay": crawl_delay,
            "pages_count": len(pages_data),
            "pages": pages_data,
        }

    # Write merged or new project JSON
    with open(project_json_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    # Check whether the JSON file was successfully created
    if project_json_path.exists():
        logger.info(f"JSON successfully written to: {project_json_path}")
    else:
        logger.error(f"Failed to write JSON: {project_json_path}")

    logger.info("Analysis completed.")
    return None


if __name__ == "__main__":
    main()
