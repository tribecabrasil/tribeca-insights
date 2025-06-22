import json
from pathlib import Path

from tribeca_insights.exporters.json import update_project_json


def test_update_project_json_creates(tmp_path: Path) -> None:
    slug = "example-com"
    pages = [{"slug": "home", "title": "Home"}]
    update_project_json(
        tmp_path,
        slug,
        "https://example.com",
        "en",
        pages,
        5,
        2,
        0.0,
        crawler_engine="BeautifulSoup",
    )
    path = tmp_path / f"project_{slug}.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project_slug"] == slug
    assert data["pages_count"] == 1
    assert data["created_at"] == data["last_updated_at"]
    assert data["crawler_engine"] == "BeautifulSoup"


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
    update_project_json(
        tmp_path,
        slug,
        "https://example.com",
        "en",
        pages,
        5,
        2,
        0.0,
        crawler_engine="BeautifulSoup",
    )
    data = json.loads(path.read_text())
    assert data["created_at"] == "2020-01-01T00:00:00"
    assert data["pages_count"] == 2
    slugs = {p["slug"] for p in data["pages"]}
    assert {"home", "about"} <= slugs
    assert data["last_updated_at"] != "2020-01-01T00:00:00"
    assert data["crawler_engine"] == "BeautifulSoup"


def test_update_project_json_fields(tmp_path: Path) -> None:
    slug = "site"
    update_project_json(
        tmp_path,
        slug,
        "https://site.com",
        "en",
        [],
        10,
        3,
        0.5,
        crawler_engine="BeautifulSoup",
    )
    data = json.loads((tmp_path / f"project_{slug}.json").read_text())
    assert data["base_url"] == "https://site.com"
    assert data["max_pages"] == 10
    assert data["max_workers"] == 3
    assert data["crawl_delay"] == 0.5
    assert data["crawler_engine"] == "BeautifulSoup"
