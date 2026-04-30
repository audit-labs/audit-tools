#!/usr/bin/env python3
"""Shared runtime helpers for GitLab collection scripts."""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
from typing import Any
from shared.python.cli import add_standard_flags
from shared.python.outputs import ensure_run_tree
from shared.python.metadata import build_metadata


def build_parser(desc: str, formats=("json",)) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--base-url", default=os.getenv("GITLAB_BASE_URL", "https://gitlab.com/api/v4"))
    p.add_argument("--private-token", default=os.getenv("GITLAB_PRIVATE_TOKEN", ""))
    return add_standard_flags(p, formats=formats)


def init_run(args, tool_name: str):
    run = ensure_run_tree(args.output_dir, tool_name)
    return run, run["root"].name


def write_artifacts(run: dict[str, Path], name: str, payload: Any):
    text = json.dumps(payload, indent=2)
    (run["raw"] / f"{name}.raw.json").write_text(text)
    (run["parsed"] / f"{name}.json").write_text(text)
    (run["evidence"] / f"{name}.json").write_text(text)


def write_meta(run, tool_name, run_id, args, counts=None, warnings=None, errors=None):
    meta = build_metadata(tool=tool_name, run_id=run_id, command=" ".join(sys.argv), record_counts=counts or {}, warnings=warnings or [], errors=errors or [])
    (run["root"] / "metadata.json").write_text(json.dumps(meta, indent=2))
