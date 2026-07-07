"""Reconciliation output helpers."""

from __future__ import annotations

import pandas as pd


def build_reconciliation(
    source_rows: int,
    blank_id_count: int,
    duplicate_id_count: int,
    excluded_rows: int,
    validated_rows: int,
    requested_sample_size: int | None,
    final_sample_size: int,
) -> pd.DataFrame:
    unsampled = validated_rows - final_sample_size
    rows = [
        ("Source rows", source_rows),
        ("Rows with blank ID", blank_id_count),
        ("Duplicate IDs", duplicate_id_count),
        ("Excluded rows", excluded_rows),
        ("Validated population rows", validated_rows),
        (
            "Requested sample size",
            "" if requested_sample_size is None else requested_sample_size,
        ),
        ("Final sample size", final_sample_size),
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
