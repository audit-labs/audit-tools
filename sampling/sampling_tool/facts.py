"""Facts about one sampling run, shared by its manifest, methodology, and
reconciliation outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunFacts:
    input_file: Path
    input_sha256: str
    input_sheet: str | None
    options: object
    effective_id_column: str | None
    id_column_omitted: bool
    source_row_count: int
    validated_population_count: int
    excluded_row_count: int
    duplicate_id_count: int
    blank_id_count: int
    requested_sample_size: int | None
    sample_size_actual: int
    random_seed: int | None
