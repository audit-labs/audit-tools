"""Shared argparse helpers and standard flags."""

from __future__ import annotations

import argparse


DEFAULT_FORMATS = ("json", "csv", "txt")


def add_standard_flags(parser: argparse.ArgumentParser, *, formats: tuple[str, ...] = DEFAULT_FORMATS) -> argparse.ArgumentParser:
    """Attach standard execution flags to a parser."""
    parser.add_argument("--output-dir", default="outputs", help="Root directory where run artifacts are written.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug output.")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error output.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without collecting evidence.")
    parser.add_argument("--format", choices=formats, default=formats[0], help="Primary parsed output format.")
    return parser


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    return add_standard_flags(parser)
