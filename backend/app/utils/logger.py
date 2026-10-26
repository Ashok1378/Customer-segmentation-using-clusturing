"""
logger.py - Centralised logging configuration with rotating file handler.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

# Resolve outputs directory relative to this file's location:
# utils/ -> app/ -> backend/ -> outputs/
_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_UTILS_DIR)
_BACKEND_DIR = os.path.dirname(_APP_DIR)
_OUTPUTS_DIR = os.path.join(_BACKEND_DIR, "outputs")

os.makedirs(_OUTPUTS_DIR, exist_ok=True)

_LOG_FILE = os.path.join(_OUTPUTS_DIR, "app.log")

_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Track already-configured loggers to avoid duplicate handlers
_configured_loggers: set = set()


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger with the given name, configured with both a rotating
    file handler (backend/outputs/app.log) and a console handler.

    Handlers are added only once per named logger even if called multiple times.
    """
    logger = logging.getLogger(name)

    if name in _configured_loggers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # ── Rotating file handler ──────────────────────────────────────────────
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB per file
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # ── Console (stream) handler ───────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent propagation to the root logger to avoid duplicate output
    logger.propagate = False

    _configured_loggers.add(name)
    return logger
