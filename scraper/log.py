import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

from rich.console import Console
from rich.logging import RichHandler


LOG_PATH = Path("logs/run.log")
LevelArg = Union[int, str]


def _resolve_level(level: LevelArg) -> int:
    """Return a numeric logging level from either an int or string value."""
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        value = getattr(logging, level.upper(), None)
        if isinstance(value, int):
            return value
        raise ValueError(f"Unknown logging level: {level}")
    raise TypeError("level must be an int or a str")


def configure_logging(level: LevelArg = "INFO", log_path: Optional[Path] = None) -> None:
    """Configure root logging with rich console and rotating file."""
    log_path = log_path or LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        # Already configured
        return

    numeric_level = _resolve_level(level)

    console_handler = RichHandler(console=Console(), markup=True, rich_tracebacks=True)
    console_handler.setLevel(numeric_level)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)
    file_handler.setLevel(numeric_level)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    root.setLevel(numeric_level)
    root.addHandler(console_handler)
    root.addHandler(file_handler)
