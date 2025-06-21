# Agents.md Guide for Tribeca Insights with OpenAI Codex

This `Agents.md` provides guidance for OpenAI Codex and similar AI agents working specifically within the Tribeca Insights project, a modular Python CLI designed for content extraction, semantic analysis, and SEO reporting.

## Project Structure for Codex Navigation

* `/tribeca_insights`: Main package

  * `/cli.py`: Entry-point for command-line interface
  * `/config.py`: Configuration settings
  * `/crawler.py`: Logic for intelligent web crawling
  * `/storage.py`: Handling of storage operations
  * `/text_utils.py`: Utilities for text cleaning, tokenization, and analysis
  * `/exporters`: Modules to generate Markdown, CSV, and JSON outputs
* `/scripts`: Auxiliary scripts
* `/tests`: Test suite Codex should maintain and extend

## Coding Conventions

* Use Python 3.10+ for all Codex-generated code
* Follow PEP 8 guidelines and Black formatter (line length ≤ 88 chars)
* Meaningful variable/function names (snake_case), classes (PascalCase), constants (UPPER_CASE)
* Comments for complex logic; descriptive and concise
* Always provide type annotations (PEP 484 and PEP 526)

## Modules and Functions

* Clearly structured, single-purpose modules
* Functions should perform one logical action
* Proper use of async/await (PEP 492) when relevant

## Docstrings (PEP 257 Windows-style)

* One-line summary followed by detailed description if needed
* Describe parameters and return types clearly

Example:

```python
def clean_text(text: str) -> str:
    """Clean text by removing unwanted characters and extra spaces.

    Args:
        text: Input text to clean.

    Returns:
        Cleaned text with standardized spacing.
    """
    pass
```

## Testing Requirements

Codex must generate tests using pytest:

```bash
pytest tests/ # Run all tests
pytest tests/test_module.py # Run specific tests
pytest --cov=tribeca_insights tests/ # Run with coverage
```

Maintain test coverage ≥80%.

## Pull Request (PR) Standards

Codex-generated PRs must:

* Include clear description and rationale
* Reference any related GitHub issues
* Ensure all tests pass
* Focus on one logical change per PR

## CI/CD and Checks

Before submitting code:

```bash
black --check .
isort --check-only .
flake8
pytest
```

All checks must pass to merge Codex-generated code.

## AI Analysis Integration (`ai_analysis`)

Codex should maintain consistency with the Tribeca Insights JSON schema (`project_{DOMAIN}.json`), populating or updating fields in `ai_analysis`:

* `embedding`: vector for semantic analysis
* `sentiment`: "positive", "neutral", "negative"
* `entities`: named entities from NLP
* `topics`: content classification
* `summary_ai`: AI-generated summary
* `faq_ai`: AI-generated FAQs
* `intent`: classified intent ("informational", "transactional")
* `quality_score_ai`: content quality score

## Usage and Workflow Commands

Codex can assist users with standard commands:

```bash
# Standard crawling execution
tribeca-insights --max-pages 50 --language en

# Validation of JSON structure
python scripts/validate_structure.py
```

## Technologies Detection

Codex should implement and extend detection heuristics:

* Parse headers, meta tags, file patterns
* Integrate external APIs (e.g., Wappalyzer, BuiltWith)

This document ensures structured and consistent Codex assistance within Tribeca Insights, enhancing AI and human collaboration efficiency.
