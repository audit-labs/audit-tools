"""Manifest generation."""

from __future__ import annotations

import json
from pathlib import Path

from . import __version__, engine
from .facts import RunFacts


def build_manifest(
    facts: RunFacts, *, run_timestamp_utc: str, output_files: list[str]
) -> dict[str, object]:
    options = facts.options
    return {
        "tool": "audit_sample",
        "version": __version__,
        "engine": engine.ENGINE,
        "engine_version": engine.ENGINE_VERSION,
        "run_timestamp_utc": run_timestamp_utc,
        "input_file": str(facts.input_file),
        "input_sha256": facts.input_sha256,
        "input_sheet": facts.input_sheet,
        "method": options.method,
        "id_column": options.id_column,
        "effective_id_column": facts.effective_id_column,
        "id_column_omitted": facts.id_column_omitted,
        "stratify_column": options.stratify_column,
        "sample_size_requested": options.sample_size,
        "sample_size_actual": facts.sample_size_actual,
        "random_seed": facts.random_seed,
        "filters": options.filters,
        "dedupe_id": options.dedupe_id,
        "exclude_blank_id": options.exclude_blank_id,
        "allow_shortfall": options.allow_shortfall,
        "source_row_count": facts.source_row_count,
        "validated_population_count": facts.validated_population_count,
        "excluded_row_count": facts.excluded_row_count,
        "duplicate_id_count": facts.duplicate_id_count,
        "blank_id_count": facts.blank_id_count,
        "output_files": output_files,
    }


def write_manifest(manifest: dict[str, object], path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
