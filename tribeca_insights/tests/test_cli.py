import json
import sys
from pathlib import Path

import pandas as pd

import tribeca_insights.cli as cli


def test_cli_calls_export_pages_json(monkeypatch, tmp_path):
    pages = [{"slug": "home", "title": "Home"}]
    called: dict[str, list] = {}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "setup_environment", lambda: None)
    monkeypatch.setattr(cli, "crawl_site", lambda *a, **k: ("", pages))
    monkeypatch.setattr(cli, "add_urls_from_sitemap", lambda base_url, df: df)
    monkeypatch.setattr(cli, "reconcile_md_files", lambda df, folder: df)
    monkeypatch.setattr(cli, "reconcile_json_files", lambda df, folder: df)
    monkeypatch.setattr(cli, "save_visited_urls", lambda df, path: None)
    monkeypatch.setattr(cli, "update_project_json", lambda *a, **k: None)
    monkeypatch.setattr(
        cli,
        "load_visited_urls",
        lambda *_args, **_kw: pd.DataFrame(
            columns=["URL", "Status", "Data", "MD File", "JSON File"]
        ),
    )

    original_setup = cli.setup_project_folder
    monkeypatch.setattr(
        cli,
        "setup_project_folder",
        lambda slug: original_setup(slug, base_path=tmp_path),
    )

    original_export = cli.export_pages_json

    def spy(folder: Path, p_data: list) -> None:
        called["pages"] = p_data
        original_export(folder, p_data)

    monkeypatch.setattr(cli, "export_pages_json", spy)

    sys.argv = [
        "prog",
        "crawl",
        "--slug",
        "example.com",
        "--base-url",
        "https://example.com",
        "--max-pages",
        "1",
    ]
    cli.main()

    assert called.get("pages") == pages
    json_file = tmp_path / "example.com" / "pages_json" / "home.json"
    assert json_file.exists()
    data = json.loads(json_file.read_text())
    assert data["slug"] == "home"
    log_file = tmp_path / "logs" / "tribeca-insights.log"
    assert log_file.exists(), "Log file was not created"


def test_cli_playwright_flag(monkeypatch, tmp_path):
    called = {}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "setup_environment", lambda: None)

    def crawl(*a, **k):
        called["playwright"] = k.get("use_playwright")
        return "", []

    monkeypatch.setattr(cli, "crawl_site", crawl)
    monkeypatch.setattr(cli, "add_urls_from_sitemap", lambda base_url, df: df)
    monkeypatch.setattr(cli, "reconcile_md_files", lambda df, folder: df)
    monkeypatch.setattr(cli, "reconcile_json_files", lambda df, folder: df)
    monkeypatch.setattr(cli, "save_visited_urls", lambda df, path: None)
    monkeypatch.setattr(cli, "update_project_json", lambda *a, **k: None)
    monkeypatch.setattr(
        cli,
        "load_visited_urls",
        lambda *_args, **_kw: pd.DataFrame(
            columns=["URL", "Status", "Data", "MD File", "JSON File"]
        ),
    )
    original_setup = cli.setup_project_folder
    monkeypatch.setattr(
        cli,
        "setup_project_folder",
        lambda slug: original_setup(slug, base_path=tmp_path),
    )

    sys.argv = [
        "prog",
        "crawl",
        "--slug",
        "example.com",
        "--base-url",
        "https://example.com",
        "--playwright",
    ]
    cli.main()
    assert called.get("playwright") is True
