"""Shared logging setup helpers for audit scripts."""

from __future__ import annotations

import logging
import sys


def configure_logger(
    name: str, *, verbose: bool = False, quiet: bool = False
) -> logging.Logger:
    """Build a stdout/stderr aware logger with predictable behavior."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    info_level = logging.DEBUG if verbose else logging.INFO
    stdout_level = logging.WARNING if quiet else info_level
    warn_level = logging.ERROR if quiet else logging.WARNING

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(stdout_level)
    stdout_handler.addFilter(lambda rec: rec.levelno < logging.WARNING)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(warn_level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    return logger
