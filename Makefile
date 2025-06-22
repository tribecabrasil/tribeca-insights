.PHONY: help venv-check install init test lint format typecheck crawl export-csv export-json export-md run clean clean-all

help: ## Show available make targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk -F ':.*?## ' '{ printf "\033[36m%-15s\033[0m %s\n", $$1, $$2 }'

venv-check: ## Check if virtual environment is activated
	@if [ -z "$${VIRTUAL_ENV}" ]; then \
	    echo "⚠️  Virtual environment not detected. It's strongly recommended to run 'python -m venv .venv && source .venv/bin/activate' before proceeding."; \
	fi

install: venv-check ## Install Python dependencies and NLTK resources
	@pip install --upgrade pip
	@pip install -e .
	@pip install certifi
	@python -c "import os, certifi; os.environ.setdefault('SSL_CERT_FILE', certifi.where()); import nltk; nltk.download('stopwords')"

init: install ## Bootstrap project (recommended before first run)

test: ## Run all tests
	pytest -vv

lint: ## Run black, isort, flake8 checks
	black --check .
	isort --check-only .
	flake8

format: ## Format code using black and isort
	black .
	isort .

typecheck: ## Run static type checks
	mypy .
	pyright

crawl: ## Run crawl with SLUG and BASE_URL (e.g. make crawl SLUG=example.com BASE_URL=https://example.com)
        tribeca-insights crawl --slug=$(SLUG) --base-url=$(BASE_URL) --max-pages=20 --language=en $(if $(PLAYWRIGHT),--playwright,)

export-csv: ## Export CSV from last crawl
	tribeca-insights export --slug=$(SLUG) --format=csv

export-json: ## Export JSON from last crawl
	tribeca-insights export --slug=$(SLUG) --format=json

export-md: ## Export Markdown from last crawl
	tribeca-insights export --slug=$(SLUG) --format=markdown

run: ## Run default crawl (example.com)
	tribeca-insights crawl example.com --base-url https://example.com --language en --max-pages 20

clean: ## Remove generated outputs and caches
	rm -rf example-com/ __pycache__/ .pytest_cache htmlcov report.csv report.json pages_md

clean-all: ## Remove all generated artifacts
	./cleanup.sh
