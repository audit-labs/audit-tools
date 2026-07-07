from types import SimpleNamespace

import pandas as pd
import pytest

from sampling.sampling_tool.cli import run
from sampling.sampling_tool.io import AuditSamplingError


def _options(input_path, out_path, **kwargs):
    values = {
        "input": str(input_path),
        "sheet": None,
        "id_column": "ID",
        "method": "validate-only",
        "sample_size": None,
        "stratify_column": None,
        "strata_counts": None,
        "strata_proportions": None,
        "seed": None,
        "out": str(out_path),
        "exclude_blank_id": False,
        "dedupe_id": "fail",
        "filters": {},
        "allow_shortfall": False,
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_duplicate_ids_fail_by_default_and_write_duplicate_file(tmp_path):
    source = tmp_path / "population.csv"
    pd.DataFrame({"ID": ["A", "A", "B"], "Status": ["Closed"] * 3}).to_csv(
        source, index=False
    )

    with pytest.raises(AuditSamplingError):
        run(_options(source, tmp_path / "out"))

    run_dir = next((tmp_path / "out").glob("sample_*"))
    duplicates = pd.read_csv(run_dir / "duplicate_ids.csv")
    assert duplicates["ID"].tolist() == ["A", "A"]


def test_blank_ids_are_excluded_when_requested(tmp_path):
    source = tmp_path / "population.csv"
    pd.DataFrame({"ID": ["A", "", "B"], "Status": ["Closed"] * 3}).to_csv(
        source, index=False
    )

    run_dir = run(_options(source, tmp_path / "out", exclude_blank_id=True))

    validated = pd.read_csv(run_dir / "population_validated.csv")
    excluded = pd.read_csv(run_dir / "excluded_rows.csv")
    assert len(validated) == 2
    assert excluded["_exclusion_reason"].tolist() == ["Blank ID"]


def test_filters_reduce_population_and_write_excluded_rows(tmp_path):
    source = tmp_path / "population.csv"
    pd.DataFrame(
        {"ID": ["A", "B", "C"], "Status": ["Closed", "Open", "Closed"]}
    ).to_csv(source, index=False)

    run_dir = run(_options(source, tmp_path / "out", filters={"Status": "Closed"}))

    validated = pd.read_csv(run_dir / "population_validated.csv")
    excluded = pd.read_csv(run_dir / "excluded_rows.csv")
    assert validated["ID"].tolist() == ["A", "C"]
    assert excluded["ID"].tolist() == ["B"]


def test_validate_only_writes_no_sample_csv(tmp_path):
    source = tmp_path / "population.csv"
    pd.DataFrame({"ID": ["A", "B", "C"], "Status": ["Closed"] * 3}).to_csv(
        source, index=False
    )

    run_dir = run(_options(source, tmp_path / "out"))

    assert not (run_dir / "sample.csv").exists()
