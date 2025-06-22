# Playwright Integration

This project can optionally render pages using Playwright for sites that rely heavily on JavaScript.

## Installation

Install the package and browser drivers:

```bash
pip install playwright
playwright install
```

Run `playwright install` once to download the required browser binaries.

## When It Runs

`crawl_site` will automatically use Playwright whenever more than three URLs are queued. You can also force rendering for every page with the `--playwright` flag.

## Enable via CLI

```bash
tribeca-insights crawl --slug example.com --base-url https://example.com --playwright
```

## Enable via Makefile

Pass `PLAYWRIGHT=1` to the `crawl` target:

```bash
make crawl SLUG=example.com BASE_URL=https://example.com PLAYWRIGHT=1
```

## Output Files

Pages renderizadas com Playwright são salvas na pasta
`pages_md_playwright/`. O índice é gerado a partir dessa pasta e da
`pages_md/` tradicional.

## Project JSON

Quando Playwright é utilizado, a função `update_project_json` grava o campo
`"crawler_engine": "Playwright"` no arquivo `project_<slug>.json`.

Exemplo:

```json
{
  "crawler_engine": "Playwright",
  "pages_count": 10
}
```
