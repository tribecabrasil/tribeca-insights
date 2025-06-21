import json
from pathlib import Path

import pandas as pd

from tribeca_insights.exporters.csv import export_csv
from tribeca_insights.exporters.json import export_json


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
