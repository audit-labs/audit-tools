# Script Standards

## Scope
Applies to all future tools and all migrated existing tools in `applications/`,
`databases/`, `os/`, and `sampling/`.

## Naming conventions
- Script/tool folder: `snake_case` control-focused name (`branch_protections`,
  `iam_assignments`).
- Main executable:
  - Python: `main.py` (or package entry point).
  - Shell: `run.sh` only when shell is justified.
- Output dataset files: `snake_case` nouns (`members.csv`, `exceptions.json`).

## CLI argument conventions (required defaults)
Every runnable tool should support:
- `--output-dir` (default: `./outputs`)
- `--format` (`csv`, `json`, or both where applicable)
- `--dry-run` (where collection side effects are possible)
- `--verbose`
- `--quiet`
- `--config <path>` (where useful)

Recommended additions:
- `--scope` (org/account/project/db target)
- `--since` / `--until` for date-bounded evidence pulls
- `--timeout`

## Input handling conventions
- Validate required scope inputs at startup.
- Validate mutually exclusive options.
- Validate date formats (`YYYY-MM-DD`) and IDs before calls.
- Reject unknown config keys with clear messages.
- Print concise usage on argument failure; exit code `2`.

## Authentication / credential handling
- Credentials must come from environment variables, profile chains, or external
  secret manager references.
- Never hard-code tokens/keys (current GitLab scripts do this; must be removed).
- Never echo raw credentials in `stdout`, logs, metadata, or output files.
- Log only credential source type (e.g., `auth_source: env:GITHUB_TOKEN`).

## Logging conventions
- Dual-mode logging:
  - Human-readable console summary.
  - Structured run log at `logs/run.log` (timestamp + level + event).
- Levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- Start and end of each collection step must be logged.

## Error handling conventions
- Fail safely (no destructive actions).
- Continue non-dependent collectors when one collector fails.
- Record step-level errors in `exceptions/` and `metadata.json`.
- Return non-zero if any required collection failed.
- Standard exit codes:
  - `0`: success (possibly with warnings)
  - `1`: collection failure
  - `2`: invalid arguments/config
  - `3`: authentication failure

## Script template (recommended)
1. Parse args.
2. Resolve config + credentials.
3. Build deterministic `run_id` and output paths.
4. Validate scope and prerequisites.
5. Collect raw evidence.
6. Normalize parsed outputs.
7. Emit exceptions and metadata.
8. Print summary + proper exit code.

## Security constraints
- Read-only behavior unless explicitly documented and opt-in.
- Minimum API permissions documented per tool.
- Redact identity fields only when legally required; otherwise preserve audit
  traceability.
- Protect PII/secret-bearing outputs through clear warnings and optional masking
  flags.
