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

## Output Directory

Pages rendered by Playwright are stored in `pages_md_playwright/` within
your project folder. This supplements the standard `pages_md/` directory
used for pages fetched without a browser.

## Project JSON

The helper `update_project_json` tracks the crawler engine. When Playwright
is used, it writes `"crawler_engine": "Playwright"` to
`project_<slug>.json`:

```json
{
  "project_slug": "example-com",
  "crawled_by": "Tribeca Insights",
  "crawler_engine": "Playwright"
}
```
