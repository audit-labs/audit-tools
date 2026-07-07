"""Sampling methods."""

from __future__ import annotations

import math
import random

import pandas as pd

from .io import AuditSamplingError


def ensure_seed(seed: int | None) -> tuple[int, bool]:
    if seed is not None:
        return int(seed), False
    return random.SystemRandom().randint(1, 2_147_483_647), True


def parse_key_ints(value: str | None, label: str) -> dict[str, int]:
    if not value:
        return {}
    parsed: dict[str, int] = {}
    for part in value.split(","):
        if "=" not in part:
            raise AuditSamplingError(f"Invalid {label} entry '{part}'. Use Name=Count.")
        key, raw_count = part.split("=", 1)
        key = key.strip()
        try:
            count = int(raw_count.strip())
        except ValueError as exc:
            raise AuditSamplingError(
                f"Invalid {label} count for '{key}': {raw_count}"
            ) from exc
        if count <= 0:
            raise AuditSamplingError(f"{label} count for '{key}' must be positive.")
        parsed[key] = count
    return parsed


def parse_key_floats(value: str | None, label: str) -> dict[str, float]:
    if not value:
        return {}
    parsed: dict[str, float] = {}
    for part in value.split(","):
        if "=" not in part:
            raise AuditSamplingError(
                f"Invalid {label} entry '{part}'. Use Name=Proportion."
            )
        key, raw_proportion = part.split("=", 1)
        key = key.strip()
        try:
            proportion = float(raw_proportion.strip())
        except ValueError as exc:
            raise AuditSamplingError(
                f"Invalid {label} proportion for '{key}': {raw_proportion}"
            ) from exc
        if proportion <= 0:
            raise AuditSamplingError(
                f"{label} proportion for '{key}' must be positive."
            )
        parsed[key] = proportion
    if not math.isclose(sum(parsed.values()), 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise AuditSamplingError(f"{label} proportions must sum to 1.0.")
    return parsed


def largest_remainder_allocation(
    sample_size: int, proportions: dict[str, float]
) -> dict[str, int]:
    raw = {
        stratum: {
            "floor": math.floor(sample_size * proportion),
            "remainder": sample_size * proportion
            - math.floor(sample_size * proportion),
        }
        for stratum, proportion in proportions.items()
    }
    allocation = {stratum: values["floor"] for stratum, values in raw.items()}
    remaining = sample_size - sum(allocation.values())
    ranked = sorted(
        raw,
        key=lambda stratum: (-raw[stratum]["remainder"], stratum),
    )
    for stratum in ranked[:remaining]:
        allocation[stratum] += 1
    return allocation


def random_sample(population: pd.DataFrame, sample_size: int, seed: int) -> pd.DataFrame:
    return population.sample(n=sample_size, random_state=seed)


def stratified_sample(
    population: pd.DataFrame,
    stratify_column: str,
    counts: dict[str, int],
    seed: int,
    allow_shortfall: bool,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    samples: list[pd.DataFrame] = []
    summary: list[dict[str, object]] = []
    for index, (stratum, requested) in enumerate(counts.items()):
        stratum_population = population[population[stratify_column] == stratum]
        actual_count = min(requested, len(stratum_population))
        if actual_count < requested and not allow_shortfall:
            raise AuditSamplingError(
                f"Stratum '{stratum}' has {len(stratum_population)} rows; "
                f"requested {requested}. Use --allow-shortfall to continue."
            )
        if actual_count:
            sampled = stratum_population.sample(n=actual_count, random_state=seed + index)
            samples.append(sampled)
        summary.append(
            {
                "Stratum": stratum,
                "Population Count": len(stratum_population),
                "Requested Sample Count": requested,
                "Actual Sample Count": actual_count,
                "Shortfall": requested - actual_count,
            }
        )

    if samples:
        return pd.concat(samples), summary
    return population.iloc[0:0].copy(), summary
