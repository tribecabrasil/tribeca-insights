import json
from pathlib import Path

from tribeca_insights.exporters.json import update_project_json


def test_update_project_json_creates(tmp_path: Path) -> None:
    slug = "example-com"
    pages = [{"slug": "home", "title": "Home"}]
    update_project_json(tmp_path, slug, "https://example.com", "en", pages, 5, 2, 0.0)
    path = tmp_path / f"project_{slug}.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project_slug"] == slug
    assert data["pages_count"] == 1
    assert data["created_at"] == data["last_updated_at"]


def test_update_project_json_updates(tmp_path: Path) -> None:
    slug = "example-com"
    existing = {
        "project_slug": slug,
        "created_at": "2020-01-01T00:00:00",
        "last_updated_at": "2020-01-01T00:00:00",
        "pages": [{"slug": "home", "title": "Old"}],
        "pages_count": 1,
    }
    path = tmp_path / f"project_{slug}.json"
    path.write_text(json.dumps(existing))
    pages = [
        {"slug": "home", "title": "New"},
        {"slug": "about", "title": "About"},
    ]
    update_project_json(tmp_path, slug, "https://example.com", "en", pages, 5, 2, 0.0)
    data = json.loads(path.read_text())
    assert data["created_at"] == "2020-01-01T00:00:00"
    assert data["pages_count"] == 2
    slugs = {p["slug"] for p in data["pages"]}
    assert {"home", "about"} <= slugs
    assert data["last_updated_at"] != "2020-01-01T00:00:00"
