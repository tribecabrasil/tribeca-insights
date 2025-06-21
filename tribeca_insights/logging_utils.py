import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

DEFAULT_LOG_DIR = Path("logs")


def setup_logging(log_dir: Path = DEFAULT_LOG_DIR) -> None:
    """Configure rotating file logging under the given directory."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "tribeca-insights.log"
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter(fmt))
    logging.getLogger().addHandler(handler)
    return None
