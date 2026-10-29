"""Sampling methods."""

from __future__ import annotations

import math
import random

import pandas as pd

from . import engine
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


def random_sample(
    population: pd.DataFrame, sample_size: int, seed: int
) -> pd.DataFrame:
    return population.iloc[engine.select_random(len(population), sample_size, seed)]


def systematic_sample(
    population: pd.DataFrame, sample_size: int, seed: int
) -> pd.DataFrame:
    return population.iloc[engine.select_systematic(len(population), sample_size, seed)]


def stratified_sample(
    population: pd.DataFrame,
    stratify_column: str,
    counts: dict[str, int],
    seed: int,
    allow_shortfall: bool,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    strata = population[stratify_column].astype(str).tolist()
    try:
        positions, summary = engine.select_stratified(strata, counts, seed, allow_shortfall)
    except ValueError as exc:
        raise AuditSamplingError(f"{exc} Use --allow-shortfall to continue.") from exc
    return population.iloc[positions], summary
