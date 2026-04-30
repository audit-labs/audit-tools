# Migration Pattern (Phase 3 Pilot)

## Pilot scripts changed
- `tools/applications/aws/password_policy/gather_policy.sh`
- `tools/applications/aws/password_policy/evaluate_policy.py`

## What changed
- Added standard output tree creation via shared helpers.
- Added standardized metadata generation (`metadata.json`).
- Added common logging and explicit non-zero exit codes.
- Added optional standard flags where compatible: `--output-dir`, `--verbose`, `--quiet`, `--dry-run`, `--format`.
- Preserved legacy behavior by continuing to emit a top-level compatibility file (`policy_report.json` and `policy_audit_<run_id>.csv`).

## Standard output layout
Each run now writes to:

```text
outputs/aws_password_policy/<run_id>/
  raw/
  parsed/
  exceptions/
  evidence/
  logs/
  metadata.json
```

## Python migration pattern
1. Import shared helpers:
   - `shared/python/cli.py`
   - `shared/python/outputs.py`
   - `shared/python/logging.py`
   - `shared/python/metadata.py`
2. Keep existing positional arguments and behavior.
3. Add standard flags only when they do not break current usage.
4. Create run tree early with `ensure_run_tree(...)`.
5. Write parsed artifacts into `parsed/`; optional source dumps into `raw/`.
6. Emit `metadata.json` from `build_metadata(...)`.
7. Return explicit exit codes from `main()` and call with `raise SystemExit(main())`.

## Shell migration pattern
1. Source `shared/shell/common.sh`.
2. Reuse exit code constants (`EXIT_USAGE`, `EXIT_DEPENDENCY`, `EXIT_COLLECTION`, etc.).
3. Route operational files to run tree directories.
4. Store command stderr in `exceptions/` when useful.
5. Write metadata via `write_metadata`.
6. Preserve prior output filenames as compatibility copies when feasible.

## Compatibility rules
- Do not remove existing required positional args.
- Do not rename existing primary output without providing compatibility copy.
- New flags must be optional and default-safe.
- Keep scripts independently runnable without a framework runner.

## Validation checklist
- `rg --files`
- Python syntax check or run with safe input
- `bash -n` for shell script
- Confirm output tree creation in dry-run or real run
- Validate `metadata.json` against `shared/schemas/metadata.schema.json` when practical
- `git status --short`


## Migration status (2026-04-30)
All actively maintained executable tools should emit the standard output tree and metadata.json; legacy SQL/query artifacts remain source-only evidence templates.
