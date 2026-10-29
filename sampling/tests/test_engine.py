"""The stdlib sampling engine: stable selections, AICPA sample sizes and upper deviation limits."""

import pytest

from sampling.sampling_tool import engine

# AICPA Audit Sampling guide, sample evaluation tables (large population), upper deviation limit in %.
UDL_5 = {
    20: [14.0, 21.7, 28.3, 34.4, 40.2, 45.6, 50.8, 55.9, 60.7, 65.4, 69.9],
    25: [11.3, 17.7, 23.2, 28.2, 33.0, 37.6, 42.0, 46.3, 50.4, 54.4, 58.4],
    50: [5.9, 9.2, 12.1, 14.8, 17.4, 19.9, 22.4, 24.7, 27.1, 29.4, 31.6],
    100: [3.0, 4.7, 6.2, 7.6, 9.0, 10.3, 11.5, 12.8, 14.0, 15.2, 16.4],
    200: [1.5, 2.4, 3.2, 3.9, 4.6, 5.2, 5.8, 6.5, 7.2, 7.8, 8.4],
    500: [0.6, 1.0, 1.3, 1.6, 1.9, 2.1, 2.4, 2.7, 2.9, 3.2, 3.4],
}
UDL_10 = {
    20: [10.9, 18.1, 24.5, 30.5, 36.1, 41.5, 46.8, 51.9, 56.8, 61.6, 66.2],
    50: [4.6, 7.6, 10.3, 12.9, 15.4, 17.8, 20.2, 22.5, 24.7, 27.0, 29.2],
    100: [2.3, 3.9, 5.3, 6.6, 7.9, 9.1, 10.3, 11.5, 12.7, 13.9, 15.0],
    500: [0.5, 0.8, 1.1, 1.4, 1.6, 1.9, 2.1, 2.4, 2.6, 2.9, 3.1],
}


@pytest.mark.parametrize("risk,table", [(0.05, UDL_5), (0.10, UDL_10)])
def test_upper_deviation_limits_match_the_aicpa_tables(risk, table):
    for n, row in table.items():
        for d, published in enumerate(row):
            got = engine.upper_deviation_limit(n, d, risk)
            # Rounded up, so never below the table; the table rounds a few cells to nearest.
            assert published <= got <= round(published + 0.1, 1), (n, d, published, got)
    assert engine.upper_deviation_limit(50, 1, 0.05) == 9.2
    assert engine.upper_deviation_limit(100, 2, 0.05) == 6.2


@pytest.mark.parametrize(
    "risk,tolerable,expected,size",
    [
        (0.05, 0.05, 0.0, 59), (0.05, 0.05, 0.0025, 93), (0.05, 0.05, 0.01, 93), (0.05, 0.05, 0.0125, 124),
        (0.05, 0.05, 0.0175, 153), (0.05, 0.05, 0.02, 181), (0.05, 0.10, 0.0, 29), (0.05, 0.06, 0.0, 49),
        (0.05, 0.07, 0.0, 42), (0.05, 0.08, 0.0, 36), (0.05, 0.09, 0.0, 32), (0.05, 0.15, 0.0, 19),
        (0.05, 0.20, 0.0, 14), (0.10, 0.05, 0.0, 45), (0.10, 0.10, 0.0, 22),
    ],
)
def test_sample_sizes_match_the_aicpa_tables(risk, tolerable, expected, size):
    assert engine.attribute_sample_size(risk, tolerable, expected)["sample_size"] == size


def test_selections_are_fixed_for_a_seed():
    # Pinned so any change to the algorithm is visible; v2 selections must never drift.
    assert engine.select_random(100, 5, 20260707) == [56, 23, 65, 64, 59]
    assert sorted(engine.select_random(10, 10, 1)) == list(range(10))
    assert engine.select_systematic(100, 10, 7) == [8, 18, 28, 38, 48, 58, 68, 78, 88, 98]
    chosen, summary = engine.select_stratified(["a", "b", "a", "b", "a"], {"b": 1, "a": 2}, 3)
    assert chosen == [2, 0, 1] and [s["Stratum"] for s in summary] == ["a", "b"]
    with pytest.raises(ValueError, match="requested 3"):
        engine.select_stratified(["a"], {"a": 3}, 1)


def test_evaluation():
    res = engine.evaluate_attribute_sample(60, 0, 0.05, 0.05)
    assert res["upper_deviation_limit_pct"] == 4.9 and res["supports_reliance"] is True
    assert engine.evaluate_attribute_sample(60, 2, 0.05, 0.05)["supports_reliance"] is False
