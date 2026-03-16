"""
Logger - Global logging system
Provides unified logging functionality.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

# Global console
console = Console()

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log level map
LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Global logger cache
_loggers = {}
_initialized = False
_log_file: Optional[Path] = None


def setup_logger(
    level: str = "INFO", log_dir: Optional[str] = None, log_file: Optional[str] = None
) -> None:
    """
    Initialize the logging system.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Log directory
        log_file: Log filename
    """
    global _initialized, _log_file

    if _initialized:
        return

    log_level = LEVEL_MAP.get(level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Rich console handler
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )
    rich_handler.setLevel(log_level)
    root_logger.addHandler(rich_handler)

    # File handler (if log directory is specified)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"benchmark_{timestamp}.log"

        _log_file = log_path / log_file

        file_handler = logging.FileHandler(_log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(file_handler)

    _initialized = True

    logger = get_logger(__name__)
    logger.info(f"Logger initialized with level: {level}")
    if _log_file:
        logger.info(f"Log file: {_log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Logger instance
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]


def get_log_file() -> Optional[Path]:
    """Return the current log file path."""
    return _log_file


class LogCapture:
    """
    Log capture context manager.
    Used to capture log output from specific operations.
    """

    def __init__(self, logger_name: str = None):
        self.logger_name = logger_name
        self.captured = []
        self.handler = None

    def __enter__(self):
        self.handler = LogCaptureHandler(self.captured)

        if self.logger_name:
            logger = logging.getLogger(self.logger_name)
        else:
            logger = logging.getLogger()

        logger.addHandler(self.handler)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.logger_name:
            logger = logging.getLogger(self.logger_name)
        else:
            logger = logging.getLogger()

        logger.removeHandler(self.handler)
        return False

    def get_logs(self) -> list:
        """Return captured log records."""
        return self.captured.copy()

    def get_text(self) -> str:
        """Return captured logs as a single string."""
        return "\n".join(self.captured)


class LogCaptureHandler(logging.Handler):
    """Log capture handler."""

    def __init__(self, output_list: list):
        super().__init__()
        self.output_list = output_list
        self.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    def emit(self, record):
        self.output_list.append(self.format(record))


def log_section(title: str, char: str = "=", width: int = 60):
    """
    Print a log separator line.

    Args:
        title: Title text
        char: Separator character
        width: Total width
    """
    logger = get_logger("benchmark")
    padding = (width - len(title) - 2) // 2
    line = char * padding + f" {title} " + char * padding
    logger.info(line)


def log_dict(data: dict, title: str = None):
    """
    Pretty-print a dictionary to the log.

    Args:
        data: Dictionary to print
        title: Optional title
    """
    logger = get_logger("benchmark")
    if title:
        logger.info(f"{title}:")
    for key, value in data.items():
        logger.info(f"  {key}: {value}")
