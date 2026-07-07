from types import SimpleNamespace

import pandas as pd

from sampling.sampling_tool.cli import run


def test_reconciliation_math_ties_out(tmp_path):
    source = tmp_path / "population.csv"
    pd.DataFrame(
        {"ID": ["A", "B", "C", "D"], "Status": ["Closed", "Open", "Closed", "Open"]}
    ).to_csv(source, index=False)
    options = SimpleNamespace(
        input=str(source),
        sheet=None,
        id_column="ID",
        method="random",
        sample_size=1,
        stratify_column=None,
        strata_counts=None,
        strata_proportions=None,
        seed=7,
        out=str(tmp_path / "out"),
        exclude_blank_id=False,
        dedupe_id="fail",
        filters={"Status": "Closed"},
        allow_shortfall=False,
    )

    run_dir = run(options)
    recon = pd.read_csv(run_dir / "population_reconciliation.csv")
    metrics = dict(zip(recon["Metric"], recon["Value"]))

    assert int(metrics["Source rows"]) == 4
    assert int(metrics["Excluded rows"]) == 2
    assert int(metrics["Validated population rows"]) == 2
    assert int(metrics["Final sample size"]) == 1
    assert int(metrics["Unsampled population rows"]) == 1
    assert int(metrics["Source rows"]) == (
        int(metrics["Validated population rows"]) + int(metrics["Excluded rows"])
    )
    assert int(metrics["Validated population rows"]) == (
        int(metrics["Final sample size"]) + int(metrics["Unsampled population rows"])
    )
