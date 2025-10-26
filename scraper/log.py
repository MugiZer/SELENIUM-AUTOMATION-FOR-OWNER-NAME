import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


LOG_PATH = Path("logs/run.log")


def configure_logging(level: str = "INFO", log_path: Optional[Path] = None) -> None:
    """Configure root logging with rich console and rotating file."""
    log_path = log_path or LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        # Already configured
        return

    console_handler = RichHandler(console=Console(), markup=True, rich_tracebacks=True)
    console_handler.setLevel(level)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    root.setLevel(level)
    root.addHandler(console_handler)
    root.addHandler(file_handler)
