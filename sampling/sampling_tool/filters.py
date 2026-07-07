"""Exact-match filter parsing and application."""

from __future__ import annotations

import pandas as pd

from .io import AuditSamplingError


def parse_filters(filter_values: list[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in filter_values or []:
        if "=" not in value:
            raise AuditSamplingError(
                f"Invalid filter '{value}'. Expected format: Column=Value"
            )
        column, expected = value.split("=", 1)
        column = column.strip()
        if not column:
            raise AuditSamplingError(
                f"Invalid filter '{value}'. Filter column cannot be blank."
            )
        parsed[column] = expected.strip()
    return parsed


def apply_filters(
    population: pd.DataFrame, filters: dict[str, str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not filters:
        return population.copy(), population.iloc[0:0].copy()

    missing = [column for column in filters if column not in population.columns]
    if missing:
        raise AuditSamplingError(f"Filter column(s) not found: {', '.join(missing)}")

    keep_mask = pd.Series(True, index=population.index)
    for column, expected in filters.items():
        keep_mask &= population[column].astype("string").fillna("") == expected

    excluded = population.loc[~keep_mask].copy()
    if not excluded.empty:
        excluded["_exclusion_reason"] = "Filtered out"
    return population.loc[keep_mask].copy(), excluded
