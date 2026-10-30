"""Reconciliation output helpers."""

from __future__ import annotations

import pandas as pd

from .facts import RunFacts


def build_reconciliation(facts: RunFacts) -> pd.DataFrame:
    unsampled = facts.validated_population_count - facts.sample_size_actual
    requested_sample_size = facts.requested_sample_size
    rows = [
        ("Source rows", facts.source_row_count),
        ("Rows with blank ID", facts.blank_id_count),
        ("Duplicate IDs", facts.duplicate_id_count),
        ("Excluded rows", facts.excluded_row_count),
        ("Validated population rows", facts.validated_population_count),
        (
            "Requested sample size",
            "" if requested_sample_size is None else requested_sample_size,
        ),
        ("Final sample size", facts.sample_size_actual),
        ("Unsampled population rows", unsampled),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def build_strata_summary(summary_rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(
        summary_rows,
        columns=[
            "Stratum",
            "Population Count",
            "Requested Sample Count",
            "Actual Sample Count",
            "Shortfall",
        ],
    )
