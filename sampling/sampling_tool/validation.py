"""Validation and population preparation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .io import AuditSamplingError
from .methods import parse_key_floats, parse_key_ints


@dataclass
class ValidationResult:
    population: pd.DataFrame
    excluded_rows: pd.DataFrame
    duplicate_rows: pd.DataFrame
    effective_id_column: str
    id_column_omitted: bool
    blank_id_count: int
    duplicate_id_count: int
    warnings: list[str]
    strata_counts: dict[str, int]
    strata_proportions: dict[str, float]


def blank_id_mask(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype("string").fillna("").str.strip() == "")


def validate_and_prepare(population: pd.DataFrame, options) -> ValidationResult:
    warnings: list[str] = []
    excluded_parts: list[pd.DataFrame] = []
    working = population.copy()

    if options.id_column:
        if options.id_column not in working.columns:
            raise AuditSamplingError(f"ID column not found: {options.id_column}")
        effective_id_column = options.id_column
        id_column_omitted = False
    else:
        effective_id_column = "_audit_row_id"
        id_column_omitted = True
        working[effective_id_column] = working["_source_row_number"]
        warnings.append(
            "--id-column omitted; using _source_row_number as generated _audit_row_id."
        )

    if options.stratify_column and options.stratify_column not in working.columns:
        raise AuditSamplingError(
            f"Stratification column not found: {options.stratify_column}"
        )

    id_blank_mask = blank_id_mask(working[effective_id_column])
    blank_id_count = int(id_blank_mask.sum())
    if blank_id_count:
        if options.exclude_blank_id:
            excluded = working.loc[id_blank_mask].copy()
            excluded["_exclusion_reason"] = "Blank ID"
            excluded_parts.append(excluded)
            working = working.loc[~id_blank_mask].copy()
        else:
            warnings.append(
                f"{blank_id_count} row(s) have blank IDs and were retained."
            )

    nonblank_ids = ~blank_id_mask(working[effective_id_column])
    duplicate_mask = working.loc[nonblank_ids, effective_id_column].duplicated(
        keep=False
    )
    duplicate_rows = working.loc[nonblank_ids].loc[duplicate_mask].copy()
    duplicate_id_count = int(len(duplicate_rows))
    if duplicate_id_count:
        if options.dedupe_id == "fail":
            raise AuditSamplingError(
                f"Duplicate IDs found in '{effective_id_column}'. "
                "See duplicate_ids.csv.",
                duplicate_rows=duplicate_rows,
            )
        keep = "first" if options.dedupe_id == "first" else "last"
        drop_mask = working[effective_id_column].duplicated(keep=keep) & ~blank_id_mask(
            working[effective_id_column]
        )
        excluded = working.loc[drop_mask].copy()
        excluded["_exclusion_reason"] = f"Duplicate ID removed by dedupe={keep}"
        excluded_parts.append(excluded)
        working = working.loc[~drop_mask].copy()
        warnings.append(
            f"{len(excluded)} duplicate ID row(s) removed using dedupe={keep}."
        )

    if options.sample_size is not None and options.sample_size <= 0:
        raise AuditSamplingError("--sample-size must be a positive integer.")
    needs_sample_size = options.method == "random" or (
        options.method == "stratified" and bool(options.strata_proportions)
    )
    if needs_sample_size:
        if options.sample_size is None:
            raise AuditSamplingError(f"--sample-size is required for {options.method}.")
        if options.sample_size > len(working) and not (
            options.method == "stratified" and options.allow_shortfall
        ):
            raise AuditSamplingError(
                "--sample-size cannot exceed the validated population size."
            )

    strata_counts: dict[str, int] = {}
    strata_proportions: dict[str, float] = {}
    if options.method == "stratified":
        if not options.stratify_column:
            raise AuditSamplingError("--stratify-column is required for stratified.")
        has_counts = bool(options.strata_counts)
        has_proportions = bool(options.strata_proportions)
        if has_counts == has_proportions:
            raise AuditSamplingError(
                "Use exactly one of --strata-counts or --strata-proportions."
            )
        strata_counts = parse_key_ints(options.strata_counts, "strata")
        strata_proportions = parse_key_floats(options.strata_proportions, "strata")
        requested_strata = set(strata_counts or strata_proportions)
        actual_strata = set(working[options.stratify_column].dropna().astype(str))
        missing = sorted(requested_strata - actual_strata)
        if missing:
            raise AuditSamplingError(
                "Requested strata not found in population: " + ", ".join(missing)
            )

        if strata_counts:
            _validate_stratum_counts_fit(working, options, strata_counts)

    if excluded_parts:
        excluded_rows = pd.concat(excluded_parts, ignore_index=True)
    else:
        excluded_rows = working.iloc[0:0].copy()

    return ValidationResult(
        population=working,
        excluded_rows=excluded_rows,
        duplicate_rows=duplicate_rows,
        effective_id_column=effective_id_column,
        id_column_omitted=id_column_omitted,
        blank_id_count=blank_id_count,
        duplicate_id_count=duplicate_id_count,
        warnings=warnings,
        strata_counts=strata_counts,
        strata_proportions=strata_proportions,
    )


def _validate_stratum_counts_fit(population, options, counts: dict[str, int]) -> None:
    for stratum, requested in counts.items():
        available = int((population[options.stratify_column] == stratum).sum())
        if requested > available and not options.allow_shortfall:
            raise AuditSamplingError(
                f"Stratum '{stratum}' has {available} rows; requested {requested}. "
                "Use --allow-shortfall to continue."
            )
