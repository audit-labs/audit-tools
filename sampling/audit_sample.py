#!/usr/bin/env python3
"""Command-line entrypoint for the audit sampling tool."""

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sampling.sampling_tool.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
