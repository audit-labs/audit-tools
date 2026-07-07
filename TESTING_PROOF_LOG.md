# Testing Proof Log

Date: 2026-07-07
Repository: `/Users/cmc/git/audit-labs/audit-tools`

## Unit Tests

Command:

```bash
.venv/bin/python -m pytest sampling/tests
```

Observed output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/cmc/git/audit-labs/audit-tools
plugins: dash-4.4.0
collected 10 items

sampling/tests/test_random_sample.py ...                                 [ 30%]
sampling/tests/test_reconciliation.py .                                  [ 40%]
sampling/tests/test_stratified_sample.py ..                              [ 60%]
sampling/tests/test_validation.py ....                                   [100%]

============================== 10 passed in 0.42s ==============================
```

Result: PASS

## Manual CLI Runs

The following output packages were generated under `output/validation_suite`.
The `output` directory is ignored by git.

### Random Sample

Command:

```bash
.venv/bin/python sampling/audit_sample.py \
  --input sampling/examples/users_population.csv \
  --id-column "User ID" \
  --method random \
  --sample-size 5 \
  --seed 20260707 \
  --out ./output/validation_suite
```

Output package:

```text
output/validation_suite/sample_2026-07-07_220414
```

Observed files:

```text
manifest.json
methodology.txt
population_reconciliation.csv
population_validated.csv
run.log
sample.csv
```

Result: PASS

### Stratified Sample By Counts

Command:

```bash
.venv/bin/python sampling/audit_sample.py \
  --input sampling/examples/changes_population.csv \
  --id-column "Change ID" \
  --method stratified \
  --stratify-column "Change Type" \
  --strata-counts "Normal=3,Emergency=2,Standard=2" \
  --seed 20260707 \
  --out ./output/validation_suite
```

Output package:

```text
output/validation_suite/sample_2026-07-07_220418
```

Observed files:

```text
manifest.json
methodology.txt
population_reconciliation.csv
population_validated.csv
run.log
sample.csv
strata_summary.csv
```

Result: PASS

### Stratified Sample By Proportions

Command:

```bash
.venv/bin/python sampling/audit_sample.py \
  --input sampling/examples/changes_population.csv \
  --id-column "Change ID" \
  --method stratified \
  --stratify-column "Change Type" \
  --strata-proportions "Normal=0.50,Emergency=0.25,Standard=0.25" \
  --sample-size 8 \
  --seed 20260707 \
  --out ./output/validation_suite
```

Output package:

```text
output/validation_suite/sample_2026-07-07_220425
```

Observed files:

```text
manifest.json
methodology.txt
population_reconciliation.csv
population_validated.csv
run.log
sample.csv
strata_summary.csv
```

Result: PASS

### Validate-Only With Filter

Command:

```bash
.venv/bin/python sampling/audit_sample.py \
  --input sampling/examples/changes_population.csv \
  --id-column "Change ID" \
  --method validate-only \
  --filter "Status=Closed" \
  --out ./output/validation_suite
```

Output package:

```text
output/validation_suite/sample_2026-07-07_220430
```

Observed files:

```text
excluded_rows.csv
manifest.json
methodology.txt
population_reconciliation.csv
population_validated.csv
run.log
```

Result: PASS. No `sample.csv` was produced, as expected for validate-only.

### YAML Config Run

Command:

```bash
.venv/bin/python sampling/audit_sample.py \
  --config sampling/examples/stratified_config.yml \
  --out ./output/validation_suite
```

Output package:

```text
output/validation_suite/sample_2026-07-07_220436
```

Observed files:

```text
manifest.json
methodology.txt
population_reconciliation.csv
population_validated.csv
run.log
sample.csv
strata_summary.csv
```

Result: PASS

### Duplicate-ID Failure Evidence

Command:

```bash
.venv/bin/python sampling/audit_sample.py \
  --input /private/tmp/audit_sample_validation_inputs/duplicate_ids.csv \
  --id-column ID \
  --method validate-only \
  --out ./output/validation_suite
```

Output package:

```text
output/validation_suite/sample_2026-07-07_220453
```

Observed files:

```text
duplicate_ids.csv
manifest.json
methodology.txt
population_reconciliation.csv
population_validated.csv
run.log
```

Result: PASS. The command failed as intended because duplicate IDs are rejected
by default, and `duplicate_ids.csv` was still written as evidence.

### Blank-ID Exclusion Evidence

Command:

```bash
.venv/bin/python sampling/audit_sample.py \
  --input /private/tmp/audit_sample_validation_inputs/blank_ids.csv \
  --id-column ID \
  --method validate-only \
  --exclude-blank-id \
  --out ./output/validation_suite
```

Output package:

```text
output/validation_suite/sample_2026-07-07_220500
```

Observed files:

```text
excluded_rows.csv
manifest.json
methodology.txt
population_reconciliation.csv
population_validated.csv
run.log
```

Result: PASS. Blank-ID rows were excluded and written to `excluded_rows.csv`.

## Output Integrity Validation

Command:

```bash
.venv/bin/python - <<'PY'
# Programmatic validation over output/validation_suite:
# - required files by method
# - manifest required keys
# - manifest output_files matches files on disk
# - reconciliation tie-outs
# - population_validated row counts and _source_row_number
# - sample.csv metadata columns and counts
# - strata_summary schema and counts
# - excluded_rows.csv evidence
# - duplicate_ids.csv evidence
# - run.log final status
PY
```

Observed output:

```text
Validated 7 output package(s).
sample_2026-07-07_220414: method=random, status=success, file_count=6
sample_2026-07-07_220418: method=stratified, status=success, file_count=7
sample_2026-07-07_220425: method=stratified, status=success, file_count=7
sample_2026-07-07_220430: method=validate-only, status=success, file_count=6
sample_2026-07-07_220436: method=stratified, status=success, file_count=7
sample_2026-07-07_220453: method=validate-only, status=failed, file_count=6
sample_2026-07-07_220500: method=validate-only, status=success, file_count=6
All output package integrity checks passed.
```

Result: PASS

## Overall Result

All automated tests passed, all manual CLI paths completed with expected
behavior, and all generated output packages passed integrity validation.
