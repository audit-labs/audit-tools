"""Helpers to generate standardized metadata artifacts."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_metadata(
    *,
    tool: str,
    run_id: str,
    command: str,
    scope: dict | None = None,
    record_counts: dict | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict:
    return {
        "tool": tool,
        "run_id": run_id,
        "timestamp_utc": utc_now_iso(),
        "command": command,
        "scope": scope or {},
        "record_counts": record_counts or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }
