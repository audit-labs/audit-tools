"""Shared output path and run directory helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def generate_run_id(now: datetime | None = None) -> str:
    ts = now or datetime.now(timezone.utc)
    return ts.strftime("%Y%m%dT%H%M%SZ")


def ensure_run_tree(output_dir: str | Path, tool_name: str, run_id: str | None = None) -> dict[str, Path]:
    root = Path(output_dir).expanduser().resolve() / tool_name / (run_id or generate_run_id())
    paths = {
        "root": root,
        "raw": root / "raw",
        "parsed": root / "parsed",
        "exceptions": root / "exceptions",
        "evidence": root / "evidence",
        "logs": root / "logs",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths
