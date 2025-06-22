import json
from pathlib import Path

import pandas as pd

from tribeca_insights.exporters.csv import export_csv
from tribeca_insights.exporters.json import export_json
from tribeca_insights.exporters.markdown import (
    MD_PAGES_DIR,
    MD_PAGES_PLAYWRIGHT_DIR,
    export_index_markdown,
    export_page_to_markdown,
)


def test_export_json(tmp_path: Path) -> None:
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "a.json").write_text(json.dumps({"slug": "a", "text": "x"}))
    (pages / "b.json").write_text(json.dumps({"slug": "b", "text": "y"}))
    out = tmp_path / "combined.json"
    export_json(str(pages), str(out))
    data = json.loads(out.read_text())
    assert {d["slug"] for d in data} == {"a", "b"}


def test_export_csv(monkeypatch, tmp_path: Path) -> None:
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "p1.json").write_text(json.dumps({"text": "hello world"}))
    (pages / "p2.json").write_text(json.dumps({"text": "hello data"}))

    def fake_tokenize(text: str, language: str = "english") -> list[str]:
        return text.split()

    monkeypatch.setattr(
        "tribeca_insights.exporters.csv.clean_and_tokenize", fake_tokenize
    )
    out = tmp_path / "freq.csv"
    export_csv(str(pages), str(out))
    csv_path = tmp_path / "keyword_frequency_freq.csv"
    df = pd.read_csv(csv_path)
    counts = dict(zip(df.word, df.freq))
    assert counts["hello"] == 2
    assert counts["world"] == 1


def test_export_page_to_markdown_subdirectory(tmp_path: Path) -> None:
    html = "<html><head><title>T</title></head><body></body></html>"
    export_page_to_markdown(
        tmp_path,
        "https://example.com",
        html,
        "example.com",
        set(),
        subdirectory=MD_PAGES_PLAYWRIGHT_DIR,
    )
    md_file = tmp_path / MD_PAGES_PLAYWRIGHT_DIR / "home.md"
    assert md_file.exists()


def test_export_index_markdown_multiple_dirs(tmp_path: Path) -> None:
    pages_dir = tmp_path / MD_PAGES_DIR
    pages_dir.mkdir()
    (pages_dir / "a.md").write_text("a")
    pw_dir = tmp_path / MD_PAGES_PLAYWRIGHT_DIR
    pw_dir.mkdir()
    (pw_dir / "b.md").write_text("b")
    export_index_markdown(tmp_path, [MD_PAGES_DIR, MD_PAGES_PLAYWRIGHT_DIR])
    index_path = tmp_path / "index.md"
    content = index_path.read_text()
    assert "pages_md/a.md" in content
    assert "pages_md_playwright/b.md" in content
