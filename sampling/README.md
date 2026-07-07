# Audit Sampling Tools

This directory contains simple audit sampling utilities. The production-ready
CLI is `audit_sample.py`; the older `sample.py`, `sample.html`, and
`stratified_sample.py` examples remain for compatibility and learning.

## Purpose

`audit_sample.py` generates reproducible, documented samples from CSV and Excel
populations. Each run writes the selected sample, validated population,
reconciliation files, methodology notes, a manifest, and a log suitable for an
audit workpaper package.

## Installation

Install the repository requirements:

```bash
pip install -r requirements.txt
```

Supported input formats are `.csv`, `.xlsx`, `.xls`, and `.xlsm`.

## Random Sampling Example

```bash
python sampling/audit_sample.py \
  --input sampling/examples/users_population.csv \
  --id-column "User ID" \
  --method random \
  --sample-size 5 \
  --seed 20260707 \
  --out ./output
```

## Stratified Counts Example

```bash
python sampling/audit_sample.py \
  --input sampling/examples/changes_population.csv \
  --id-column "Change ID" \
  --method stratified \
  --stratify-column "Change Type" \
  --strata-counts "Normal=3,Emergency=2,Standard=2" \
  --seed 20260707 \
  --out ./output
```

## Stratified Proportions Example

```bash
python sampling/audit_sample.py \
  --input sampling/examples/changes_population.csv \
  --id-column "Change ID" \
  --method stratified \
  --stratify-column "Change Type" \
  --strata-proportions "Normal=0.50,Emergency=0.25,Standard=0.25" \
  --sample-size 8 \
  --seed 20260707 \
  --out ./output
```

## Validate-Only Example

```bash
python sampling/audit_sample.py \
  --input sampling/examples/changes_population.csv \
  --id-column "Change ID" \
  --method validate-only \
  --filter "Status=Closed" \
  --out ./output
```

YAML config files are also supported. CLI arguments override config values:

```bash
python sampling/audit_sample.py --config sampling/examples/stratified_config.yml
```

## Output Files

Each run creates `sample_<YYYY-MM-DD>_<HHMMSS>` under the selected output
directory.

- `sample.csv`: selected sample rows for random and stratified runs.
- `population_validated.csv`: population after filters, blank-ID handling, and
  dedupe handling.
- `population_reconciliation.csv`: row-count tie-out metrics.
- `excluded_rows.csv`: rows removed by filters, blank-ID exclusion, or dedupe.
- `duplicate_ids.csv`: duplicate ID rows when duplicates are identified.
- `strata_summary.csv`: requested and actual counts for stratified runs.
- `methodology.txt`: audit workpaper narrative.
- `manifest.json`: machine-readable run metadata, input hash, options, and
  output list.
- `run.log`: start time, warnings, errors, output folder, and status.

## Reproducibility

Provide `--seed` to make row selection reproducible for the same input and
options. If no seed is provided for sampling, the tool generates one, prints a
warning, and records the generated seed in `manifest.json` and
`methodology.txt`.

The tool samples without replacement. Stratified sampling derives each stratum
seed from the base seed by adding the stratum index.

## Limitations

Filters are exact matches in `Column=Value` form only. The tool does not yet
perform monetary-unit sampling or statistical sample-size calculation.
