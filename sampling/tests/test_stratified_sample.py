from types import SimpleNamespace

import pandas as pd

from sampling.sampling_tool.cli import run


def _write_population(path):
    frame = pd.DataFrame(
        {
            "ID": [f"ID{i:03d}" for i in range(12)],
            "Type": ["A"] * 5 + ["B"] * 4 + ["C"] * 3,
        }
    )
    frame.to_csv(path, index=False)


def _options(input_path, out_path, **kwargs):
    values = {
        "input": str(input_path),
        "sheet": None,
        "id_column": "ID",
        "method": "stratified",
        "sample_size": None,
        "stratify_column": "Type",
        "strata_counts": "A=2,B=2,C=1",
        "strata_proportions": None,
        "seed": 50,
        "out": str(out_path),
        "exclude_blank_id": False,
        "dedupe_id": "fail",
        "filters": {},
        "allow_shortfall": False,
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_stratified_counts_select_exact_requested_counts(tmp_path):
    source = tmp_path / "population.csv"
    _write_population(source)

    run_dir = run(_options(source, tmp_path / "out"))

    counts = pd.read_csv(run_dir / "sample.csv")["Type"].value_counts().to_dict()
    assert counts == {"A": 2, "B": 2, "C": 1}


def test_stratified_proportions_use_largest_remainder(tmp_path):
    source = tmp_path / "population.csv"
    _write_population(source)

    run_dir = run(
        _options(
            source,
            tmp_path / "out",
            sample_size=7,
            strata_counts=None,
            strata_proportions="A=0.50,B=0.30,C=0.20",
        )
    )

    sample = pd.read_csv(run_dir / "sample.csv")
    counts = sample["Type"].value_counts().to_dict()
    assert len(sample) == 7
    assert counts == {"A": 4, "B": 2, "C": 1}
