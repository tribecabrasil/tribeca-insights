"""
validate_structure.py

Verify that each core module exports exactly the expected functions and constants.
"""

import ast
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Defina aqui o esperado para cada arquivo
EXPECTED = {
    "cli.py": ["ask_for_domain", "setup_environment"],
    "config.py": [
        "VERSION",
        "USER_AGENT",
        "CRAWLED_BY",
        "crawl_delay",
        "get_crawl_delay",
        "session",
    ],
    "text_utils.py": ["safe_strip", "clean_and_tokenize", "extract_visible_text"],
    "storage.py": [
        "load_visited_urls",
        "save_visited_urls",
        "reconcile_md_files",
        "add_urls_from_sitemap",
    ],
    "crawler.py": ["fetch_and_process", "crawl_site"],
    "exporters/markdown.py": ["export_page_to_markdown", "export_index_markdown"],
    "exporters/csv.py": ["update_keyword_frequency", "export_external_urls"],
    "exporters/json.py": [
        "export_pages_json",
        "export_index_json",
        "export_external_urls_json",
        "export_keyword_frequency_json",
        "export_visited_urls_json",
    ],
}

base = Path("tribeca_insights")
errors = False

for rel_path, keys in EXPECTED.items():
    path = base / rel_path
    if not path.exists():
        logger.error(f"File not found: {rel_path}")
        errors = True
        continue

    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            found.append(node.name)
        elif isinstance(node, ast.Assign):
            # captura constantes simples
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found.append(target.id)

    missing = set(keys) - set(found)
    extra = set(found) - set(keys) - set(["__all__"])
    if missing:
        logger.warning(f"In {rel_path}, missing symbols: {sorted(missing)}")
        errors = True
    if extra:
        logger.warning(f"In {rel_path}, unexpected symbols: {sorted(extra)}")
        errors = True

if not errors:
    logger.info("All modules contain exactly the expected symbols.")
else:
    logger.error("Please fix the above modules.")

sys.exit(0 if not errors else 1)
