from types import SimpleNamespace

import pandas as pd

from sampling.sampling_tool.cli import run


def _write_population(path, rows=20):
    frame = pd.DataFrame(
        {
            "ID": [f"ID{i:03d}" for i in range(rows)],
            "Status": ["Closed"] * rows,
        }
    )
    frame.to_csv(path, index=False)


def _options(input_path, out_path, seed=123, sample_size=5, method="random", **kwargs):
    values = {
        "input": str(input_path),
        "sheet": None,
        "id_column": "ID",
        "method": method,
        "sample_size": sample_size,
        "stratify_column": None,
        "strata_counts": None,
        "strata_proportions": None,
        "seed": seed,
        "out": str(out_path),
        "exclude_blank_id": False,
        "dedupe_id": "fail",
        "filters": {},
        "allow_shortfall": False,
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_random_sample_returns_correct_size(tmp_path):
    source = tmp_path / "population.csv"
    _write_population(source)

    run_dir = run(_options(source, tmp_path / "out"))

    sample = pd.read_csv(run_dir / "sample.csv")
    assert len(sample) == 5


def test_same_seed_returns_same_selected_ids(tmp_path):
    source = tmp_path / "population.csv"
    _write_population(source)

    first = run(_options(source, tmp_path / "out1", seed=20260707))
    second = run(_options(source, tmp_path / "out2", seed=20260707))

    first_ids = pd.read_csv(first / "sample.csv")["ID"].tolist()
    second_ids = pd.read_csv(second / "sample.csv")["ID"].tolist()
    assert first_ids == second_ids


def test_different_seed_can_return_different_selected_ids(tmp_path):
    source = tmp_path / "population.csv"
    _write_population(source)

    first = run(_options(source, tmp_path / "out1", seed=1))
    second = run(_options(source, tmp_path / "out2", seed=2))

    first_ids = pd.read_csv(first / "sample.csv")["ID"].tolist()
    second_ids = pd.read_csv(second / "sample.csv")["ID"].tolist()
    assert first_ids != second_ids
