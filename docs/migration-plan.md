# Phased Migration Plan

## Current-state inconsistencies to address first
1. Hardcoded credentials/tokens in scripts (notably GitLab scripts).
2. Non-standard output paths and file naming.
3. Mixed CLI conventions and lack of config validation.
4. Inconsistent docs depth and format.
5. Missing tests and lint/format enforcement.

## Proposed phases

### Phase 0 — Baseline and guardrails
- Add standards docs (this commit).
- Add `.gitignore` rules for `outputs/` and temporary files.
- Add minimal CI checks for lint/test placeholders.

### Phase 1 — Shared runtime foundation
- Introduce shared utility module (Python) for:
  - argument patterns,
  - output path creation,
  - metadata writer,
  - logging helper,
  - safe error/reporting patterns.
- Add shell helper snippets for standardized folder creation and metadata stubs.

### Phase 2 — Highest-risk script remediation
- Migrate scripts with hardcoded secrets first (GitLab).
- Standardize auth input through env/config.
- Ensure no credentials appear in output/logs.

### Phase 3 — Output normalization
- Update GitHub, AWS, Linux scripts to emit standard folder structure.
- Preserve existing files where possible, but route them into `raw/`, `parsed/`, `exceptions/`, `evidence/`, `logs/`.
- Add `metadata.json` to every tool run.

### Phase 4 — Documentation normalization
- Convert root `README.org` to `README.md` (or maintain both temporarily with one canonical source).
- Add per-tool README sections per standard template.
- Add sample outputs and schema notes.

### Phase 5 — Testing and quality gates
- Add unit tests for parsers/normalizers.
- Add smoke tests for CLI invocation (`--dry-run`).
- Add lint/format tooling and CI gate.

## Risks and tradeoffs
- **Risk**: Over-standardization slows contributor adoption.
  - **Mitigation**: keep mandatory core small; provide templates.
- **Risk**: Shell and Python parity is hard.
  - **Mitigation**: standardize outputs/metadata first, internals second.
- **Risk**: Existing users depend on old output file paths.
  - **Mitigation**: transition period with compatibility symlinks or duplicate writes.

## Open questions for implementation pass
1. Should Python become the default for new tools, with shell only for platform-native commands?
2. Is `pyproject.toml` acceptable as primary dependency source while retaining `requirements.txt` export?
3. Which scripts are considered authoritative for each control area where duplicates exist?
4. What minimum supported Python version should be declared?

## Specific files likely needing changes early
- `applications/gitlab/*.py` (credential handling + CLI + structured output).
- `applications/aws/*.sh` and `applications/aws/aws_password_policy/*` (output normalization + metadata).
- `applications/github/audit.py` and reporters (new output tree + metadata schema).
- `os/linux/*.sh` (sudo behavior documentation, standardized output + logging).
- `README.org` and all per-tool README files (template alignment).
