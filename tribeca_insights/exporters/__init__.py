from tribeca_insights.exporters.csv import export_csv
from tribeca_insights.exporters.json import export_json
from tribeca_insights.exporters.markdown import export_markdown


def export_data(slug: str, fmt: str) -> None:
    """
    Export crawled pages data to the specified format.

    Args:
        slug: Site identifier (e.g., "next-health.com")
        fmt: Output format (csv, json, markdown)
    """
    input_dir = f"{slug}/pages_json"
    if fmt == "csv":
        export_csv(input_dir, f"{slug}/report.csv")
    elif fmt == "json":
        export_json(input_dir, f"{slug}/report.json")
    elif fmt == "markdown":
        export_markdown(input_dir, f"{slug}/pages_md")
    else:
        raise ValueError(f"Unsupported export format: {fmt}")
