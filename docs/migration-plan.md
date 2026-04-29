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

## Implementation decisions (resolved)
1. **Default language for new tools**: Python is the default for new tooling. Shell should be limited to platform-native orchestration/collection where Python cannot replace native command usage cleanly.
2. **Dependency management**: Use `pyproject.toml` as the primary source of Python dependencies and tooling configuration, while continuing to export/maintain `requirements.txt` for compatibility.
3. **Authoritative scripts per control area**: Each control area should have one canonical script. If multiple scripts exist, keep alternatives only when there is a documented tradeoff (for example, compatibility/performance/privilege differences), and record the canonical-vs-alternative roles in the local README.
4. **Minimum Python version**: Declare Python 3 as the minimum supported baseline.

## Specific files likely needing changes early
- `applications/gitlab/*.py` (credential handling + CLI + structured output).
- `applications/aws/*.sh` and `applications/aws/aws_password_policy/*` (output normalization + metadata).
- `applications/github/audit.py` and reporters (new output tree + metadata schema).
- `os/linux/*.sh` (sudo behavior documentation, standardized output + logging).
- `README.org` and all per-tool README files (template alignment).
