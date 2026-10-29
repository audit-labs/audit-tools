"""The sampling engine: one deterministic, standard-library selection algorithm.

The same seed selects the same items on every install, with or without
pandas, in the `audit-sample` command and in audit-workbench. Each stream is
seeded from a string (`audit-sample:<seed>` and, per stratum,
`audit-sample:<seed>:<stratum>`), which Python's `random` hashes the same way
on every platform. Selections are lists of 0-based row positions.

Also here: attribute sample sizes and upper deviation limits from the
binomial distribution (large-population tables, as in the AICPA Audit
Sampling guide), and default control-frequency sample sizes.
"""

from __future__ import annotations

import math
import random
from decimal import ROUND_CEILING, Decimal

ENGINE = "audit-sample-engine"
ENGINE_VERSION = "2"

# Sample sizes by control frequency, for controls tested without statistical sizing.
# Firms can override these (audit-workbench reads `sampling_presets` from engagement.yaml).
FREQUENCY_PRESETS = {
    "annual": 1,
    "quarterly": 2,
    "monthly": 2,
    "weekly": 5,
    "daily": 20,
    "multiple-times-daily": 25,
}


def _rng(seed: int, stratum: str | None = None) -> random.Random:
    return random.Random(f"audit-sample:{seed}" + ("" if stratum is None else f":{stratum}"))


def select_random(population_size: int, sample_size: int, seed: int) -> list[int]:
    """Positions of a simple random sample without replacement, in selection order."""
    if not 0 < sample_size <= population_size:
        raise ValueError(f"sample size {sample_size} must be between 1 and the population size {population_size}")
    return _rng(seed).sample(range(population_size), sample_size)


def select_systematic(population_size: int, sample_size: int, seed: int) -> list[int]:
    """Every k-th position (k = population / sample, fractional) from a random start."""
    if not 0 < sample_size <= population_size:
        raise ValueError(f"sample size {sample_size} must be between 1 and the population size {population_size}")
    interval = population_size / sample_size
    start = _rng(seed).random() * interval
    return [int(start + i * interval) for i in range(sample_size)]


def select_stratified(
    strata: list[str], counts: dict[str, int], seed: int, allow_shortfall: bool = False
) -> tuple[list[int], list[dict]]:
    """Positions sampled per stratum (`strata[i]` is row i's stratum), and a summary per stratum."""
    chosen: list[int] = []
    summary: list[dict] = []
    for stratum in sorted(counts):
        requested = counts[stratum]
        pool = [i for i, s in enumerate(strata) if s == stratum]
        actual = min(requested, len(pool))
        if actual < requested and not allow_shortfall:
            raise ValueError(f"Stratum '{stratum}' has {len(pool)} rows; requested {requested}.")
        chosen.extend(_rng(seed, stratum).sample(pool, actual) if actual else [])
        summary.append(
            {
                "Stratum": stratum,
                "Population Count": len(pool),
                "Requested Sample Count": requested,
                "Actual Sample Count": actual,
                "Shortfall": requested - actual,
            }
        )
    return chosen, summary


def _binomial_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def attribute_sample_size(risk: float, tolerable_rate: float, expected_rate: float = 0.0) -> dict:
    """Smallest n whose upper deviation limit, with n × expected rate (rounded up) deviations, is within tolerance.

    `risk` is the risk of overreliance (0.05 for 95% confidence). Large-population
    (binomial) sizes, as in the AICPA tables.
    """
    if not (0 < risk < 1 and 0 < tolerable_rate < 1 and 0 <= expected_rate < tolerable_rate):
        raise ValueError("need 0 < risk < 1, 0 < tolerable rate < 1, and 0 <= expected rate < tolerable rate")
    for n in range(1, 5001):
        k = math.ceil(n * expected_rate - 1e-12)
        if _binomial_cdf(k, n, tolerable_rate) <= risk:
            return {"sample_size": n, "expected_deviations": k}
    raise ValueError("no sample size up to 5000 meets these parameters")


def upper_deviation_limit(sample_size: int, deviations: int, risk: float) -> float:
    """Upper deviation limit in percent, rounded up to one decimal (never understated)."""
    if not (0 <= deviations <= sample_size and sample_size > 0 and 0 < risk < 1):
        raise ValueError("need 0 <= deviations <= sample size and 0 < risk < 1")
    if deviations == sample_size:
        return 100.0
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if _binomial_cdf(deviations, sample_size, mid) > risk:
            lo = mid
        else:
            hi = mid
    return float(Decimal(hi * 100).quantize(Decimal("0.1"), rounding=ROUND_CEILING))


def evaluate_attribute_sample(sample_size: int, deviations: int, risk: float, tolerable_rate: float) -> dict:
    udl = upper_deviation_limit(sample_size, deviations, risk)
    return {
        "sample_size": sample_size,
        "deviations": deviations,
        "sample_rate_pct": round(100 * deviations / sample_size, 2),
        "upper_deviation_limit_pct": udl,
        "tolerable_rate_pct": round(100 * tolerable_rate, 2),
        "supports_reliance": udl <= 100 * tolerable_rate,
    }
