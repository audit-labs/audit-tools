# Shared Standardization Framework

This folder provides lightweight, reusable components for Phase 2 of repository standardization.

## Purpose

The shared framework gives future scripts a common baseline for:
- standard CLI flags and execution controls,
- consistent logging behavior,
- deterministic output directory layout,
- standardized metadata and exceptions,
- reusable JSON schema contracts.

This is intentionally minimal and script-first. It is not a heavyweight internal platform.

## Directory layout

- `python/`: reusable Python helpers (`cli.py`, `logging.py`, `outputs.py`, `metadata.py`, `errors.py`)
- `shell/common.sh`: reusable shell helpers and exit codes
- `schemas/`: JSON schema references for metadata, evidence, and exceptions
- `examples/`: sample output tree and sample JSON artifacts

## How future scripts should use this

1. Parse common CLI flags from `shared/python/cli.py` (or equivalent shell defaults).
2. Initialize logging via `shared/python/logging.py` or `shared/shell/common.sh`.
3. Create run directories with `shared/python/outputs.py` or `ensure_run_tree` in shell.
4. Write metadata using `shared/python/metadata.py` or `write_metadata` in shell.
5. Emit standardized exceptions using the shared exit code and schema model.

## Legacy migration expectations

- Existing scripts are not force-migrated in this phase.
- Backward compatibility should be preserved as scripts adopt shared helpers.
- Migration should happen incrementally by tool family, with behavior parity checks.
