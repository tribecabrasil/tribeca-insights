import ast
from pathlib import Path

# Defina aqui o esperado para cada arquivo
EXPECTED = {
    "cli.py": ["ask_for_domain", "setup_environment"],
    "config.py": ["VERSION", "USER_AGENT", "CRAWLED_BY", "crawl_delay", "get_crawl_delay", "session"],
    "text_utils.py": ["safe_strip", "clean_and_tokenize", "extract_visible_text"],
    "storage.py": ["load_visited_urls", "save_visited_urls", "reconcile_md_files", "add_urls_from_sitemap"],
    "crawler.py": ["fetch_and_process", "crawl_site"],
    "exporters/markdown.py": ["export_page_to_markdown", "gerar_indice_markdown"],
    "exporters/csv.py": ["update_keyword_frequency", "export_external_urls"],
    "exporters/json.py": [
        "export_pages_json", "export_index_json",
        "export_external_urls_json", "export_keyword_frequency_json", "export_visited_urls_json"
    ],
}

base = Path("seo_crawler")
errors = False

for rel_path, keys in EXPECTED.items():
    path = base / rel_path
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {rel_path}")
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
        print(f"⚠️ Em {rel_path}, faltam: {sorted(missing)}")
        errors = True
    if extra:
        print(f"⚠️ Em {rel_path}, funções/constantes não esperadas: {sorted(extra)}")
        errors = True

if not errors:
    print("✅ Todos os módulos contêm exatamente os símbolos esperados.")
else:
    print("❌ Ajuste os módulos acima.")