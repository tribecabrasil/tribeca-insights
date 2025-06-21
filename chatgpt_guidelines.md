# How ChatGPT Can Assist with Tribeca Insights

---

# Tribeca Insights

Repository Link: [https://github.com/tribecabrasil/tribeca-insights](https://github.com/tribecabrasil/tribeca-insights)\
Documentation: [https://github.com/tribecabrasil/tribeca-insights/blob/main/README.md](https://github.com/tribecabrasil/tribeca-insights/blob/main/README.md)

**Modular Python CLI for content extraction, term frequency analysis, and SEO reporting**

## Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/tribecabrasil/tribeca-insights.git
   cd tribeca-insights
   ```
2. Install in dev mode:
   ```bash
   pip install --upgrade pip
   pip install -e .
   ```
3. Download NLTK stopwords:
   ```bash
   python -c "import nltk; nltk.download('stopwords')"
   ```

## Usage

```bash
tribeca-insights --max-pages 50 --language en
```

- `--max-pages N` — Maximum pages to crawl
- `--language {en, pt-br, es, fr, it, de, zh-cn, ja, ru, ar}` — Site language for tokenization
- `--domain example.com` — (Optional) override base domain

## Workflow Steps

1. **Dependencies**: ensure required packages are installed.
2. **User Input**: select or enter domain/URL and choose site language by number.
3. **Project Setup**: create `<domain_slug>/` with `pages_md/` and `pages_json/`.
4. **History Load**: read `visited_urls_<domain>.csv`, reconcile missing MD files.
5. **Crawling**: fetch pages (up to max\_pages) respecting `robots.txt` & crawl-delay, extract metadata, and export Markdown.
6. **Keyword Frequency**: clean, tokenize, filter stopwords, and export `keyword_frequency_<domain>.csv` & JSON.
7. **Index Generation**: build `index.md` & `index.json` for all pages.
8. **External URLs**: export `external_urls.md` & JSON.
9. **Project Metadata**: generate `project_<domain>.json` with base URL, language, timestamps, CLI settings, and detailed `pages_data`.

## Project Structure

```
tribeca-insights/
├── scripts/
│   ├ main.py
│   ├ split_crawler.py
│   └ validate_structure.py
├── tribeca_insights/
│   ├ cli.py
│   ├ config.py
│   ├ crawler.py
│   ├ storage.py
│   ├ text_utils.py
│   └ exporters/
│       ├ csv.py
│       ├ json.py
│       └ markdown.py
├── example-com/  ← generated outputs
├── pyproject.toml
└── README.md
```

## Code Style (PEP 8)

- **Line length** ≤ 88 characters (configurable in Black).
- **Import order**: stdlib → third-party → local, with blank lines between groups.
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Indentation**: 4 spaces, no tabs.
- **Spacing**: spaces around operators and after commas, blank lines between top-level definitions.

*Format & check with:*

```bash
pip install black isort flake8
black --check .
isort --check-only .
flake8
```

## Additional PEP Recommendations

- **PEP 484 – Type Hints**: annotate function signatures and variables.
- **PEP 526 – Variable Annotations**: declare types for module-level and local variables.
- **PEP 563 – Postponed Annotation Evaluation**: delay type evaluation for forward references.
- **PEP 585 – Built-in Generics**: use native types like `list[str]`.
- **PEP 634/635/636 – Structural Pattern Matching**: use `match/case` (Python 3.10+).
- **PEP 498 – f-Strings**: for readable string interpolation.
- **PEP 572 – Assignment Expressions**: use `:=` for inline assignments.
- **PEP 492 – Async/Await**: native async support.
- **PEP 263 – Source File Encoding**: declare `# coding: utf-8`.
- **PEP 20 – The Zen of Python**: follow Pythonic principles (`import this`).

## AI Collaboration Guidelines

> **Note:** All code, modeling, comments, and docstrings must be written in **English**. README may remain in Portuguese.

1. **Clear Structure**: cohesive modules with descriptive names.
2. **PEP 257 Docstrings**: one-line summary + detailed description + parameters/returns.
3. **Type Hints**: use `list[str]`, `dict[str, int]`, etc.
4. **Automated Tests**: pytest with mocks and coverage ≥80%.
5. **Lint & Format**: Black, isort, flake8 in CI.
6. **Atomic Commits**: one logical change per commit.
7. **CI/CD Workflows**: GitHub Actions for install, lint, test, build, publish.
8. **Isolated Environments**: venv or poetry; include `requirements.txt` or `poetry.lock`.

## ChatGPT Collaboration Examples

Feel free to ask ChatGPT for:

- Code reviews and refactoring suggestions
- Generating or updating tests
- Writing or improving docstrings
- Designing database schemas or ETL pipelines
- Drafting GitHub Actions workflows

This document provides comprehensive context and guidelines to streamline collaboration with AI and human contributors on the Tribeca Insights project.

---



