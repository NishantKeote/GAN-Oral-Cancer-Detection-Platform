"""Structured logging configuration module for the OSCC Backend application."""

import logging
import sys
from typing import Optional


def setup_logging(debug: bool = False, log_level: Optional[str] = None) -> logging.Logger:
    """Configure application-wide structured logging.

    Args:
        debug: If True, sets level to DEBUG; otherwise INFO.
        log_level: Optional explicit log level override ('DEBUG', 'INFO', etc.).

    Returns:
        The configured root or application logger instance.
    """
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = logging.DEBUG if debug else logging.INFO

    # Define standard log format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Console handler outputting to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    # Configure application logger
    logger = logging.getLogger("oscc_backend")
    logger.setLevel(level)

    # Avoid duplicate handlers on reload
    if not logger.handlers:
        logger.addHandler(handler)

    logger.propagate = False

    return logger


# Default logger instance
logger = setup_logging()
