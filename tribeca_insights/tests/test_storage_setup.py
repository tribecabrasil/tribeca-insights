from pathlib import Path

from tribeca_insights.storage import setup_project_folder


def test_setup_project_folder_creates_structure(tmp_path: Path) -> None:
    slug = "example-com"
    folder = setup_project_folder(slug, base_path=tmp_path)
    assert (folder / "pages_md").exists()
    assert (folder / "pages_json").exists()
    template = folder / f"project_{slug}_template.json"
    assert template.exists(), "Project template JSON not created"
