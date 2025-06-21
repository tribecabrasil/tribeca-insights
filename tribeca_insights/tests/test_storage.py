import pandas as pd

import tribeca_insights.storage as storage


def test_load_visited_urls_empty(tmp_path):
    df = storage.load_visited_urls(tmp_path, "example")
    assert df.empty
    assert list(df.columns) == ["URL", "Status", "Data", "MD File", "JSON File"]


def test_save_and_load(tmp_path):
    csv_path = tmp_path / "visited.csv"
    df = pd.DataFrame(
        [
            {
                "URL": "http://a",
                "Status": 1,
                "Data": "",
                "MD File": "",
                "JSON File": "",
            },
            {
                "URL": "http://a",
                "Status": 2,
                "Data": "",
                "MD File": "",
                "JSON File": "",
            },
        ]
    )
    storage.save_visited_urls(df, csv_path)
    loaded = pd.read_csv(csv_path)
    assert len(loaded) == 1


def test_add_urls_from_sitemap(monkeypatch, tmp_path):
    xml = (
        "<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
        "<url><loc>https://example.com/page</loc></url></urlset>"
    )

    class FakeResp:
        status_code = 200
        content = xml.encode()

    monkeypatch.setattr(storage.session, "get", lambda url, timeout: FakeResp())
    df = pd.DataFrame(
        [
            {
                "URL": "https://example.com",
                "Status": 2,
                "Data": "",
                "MD File": "",
                "JSON File": "",
            }
        ]
    )
    new_df = storage.add_urls_from_sitemap("https://example.com", df)
    assert "https://example.com/page" in new_df["URL"].values


def test_load_visited_urls_parse_error(monkeypatch, tmp_path):
    csv = tmp_path / "visited_urls_example.csv"
    csv.write_text("bad,data")

    def bad_read(*_a, **_k):
        raise pd.errors.ParserError("boom")

    monkeypatch.setattr(pd, "read_csv", bad_read)
    df = storage.load_visited_urls(tmp_path, "example")
    assert df.empty


def test_reconcile_md_files(tmp_path):
    folder = tmp_path
    pages = folder / "pages_md"
    pages.mkdir()
    (pages / "home.md").write_text("hi")
    df = pd.DataFrame(
        [
            {
                "URL": "https://example.com/home",
                "Status": 1,
                "Data": "",
                "MD File": "",
                "JSON File": "",
            },
            {
                "URL": "https://example.com/miss",
                "Status": 1,
                "Data": "",
                "MD File": "",
                "JSON File": "",
            },
        ]
    )
    out = storage.reconcile_md_files(df, folder)
    assert out.loc[0, "MD File"] == "home.md"
    assert out.loc[1, "Status"] == 2


def test_reconcile_after_markdown_export(tmp_path):
    html = "<html><head><title>T</title></head><body>Hi</body></html>"
    from tribeca_insights.exporters.markdown import export_page_to_markdown

    export_page_to_markdown(
        tmp_path, "https://example.com/home", html, "example.com", set()
    )
    df = pd.DataFrame(
        [
            {
                "URL": "https://example.com/home",
                "Status": 1,
                "Data": "",
                "MD File": "",
                "JSON File": "",
            }
        ]
    )
    out = storage.reconcile_md_files(df, tmp_path)
    assert out.loc[0, "MD File"] == "home.md"


def test_reconcile_json_files(tmp_path):
    folder = tmp_path
    pages = folder / "pages_json"
    pages.mkdir()
    (pages / "home.json").write_text("{}")
    df = pd.DataFrame(
        [
            {
                "URL": "https://example.com/home",
                "Status": 1,
                "Data": "",
                "MD File": "",
                "JSON File": "",
            },
            {
                "URL": "https://example.com/miss",
                "Status": 1,
                "Data": "",
                "MD File": "",
                "JSON File": "",
            },
        ]
    )
    out = storage.reconcile_json_files(df, folder)
    assert out.loc[0, "JSON File"] == "home.json"
    assert out.loc[1, "Status"] == 2
