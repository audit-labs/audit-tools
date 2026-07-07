"""Manifest generation."""

from __future__ import annotations

from pathlib import Path
import json

from . import __version__


def build_manifest(
    *,
    run_timestamp_utc: str,
    input_file: Path,
    input_sha256: str,
    input_sheet: str | None,
    options,
    effective_id_column: str | None,
    id_column_omitted: bool,
    sample_size_actual: int,
    random_seed: int | None,
    source_row_count: int,
    validated_population_count: int,
    excluded_row_count: int,
    duplicate_id_count: int,
    blank_id_count: int,
    output_files: list[str],
) -> dict[str, object]:
    return {
        "tool": "audit_sample",
        "version": __version__,
        "run_timestamp_utc": run_timestamp_utc,
        "input_file": str(input_file),
        "input_sha256": input_sha256,
        "input_sheet": input_sheet,
        "method": options.method,
        "id_column": options.id_column,
        "effective_id_column": effective_id_column,
        "id_column_omitted": id_column_omitted,
        "stratify_column": options.stratify_column,
        "sample_size_requested": options.sample_size,
        "sample_size_actual": sample_size_actual,
        "random_seed": random_seed,
        "filters": options.filters,
        "dedupe_id": options.dedupe_id,
        "exclude_blank_id": options.exclude_blank_id,
        "allow_shortfall": options.allow_shortfall,
        "source_row_count": source_row_count,
        "validated_population_count": validated_population_count,
        "excluded_row_count": excluded_row_count,
        "duplicate_id_count": duplicate_id_count,
        "blank_id_count": blank_id_count,
        "output_files": output_files,
    }


def write_manifest(manifest: dict[str, object], path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
