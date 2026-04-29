# Audit-Tools Standardization Plan (Pre-Implementation)

## Purpose
This plan establishes a practical, auditor-friendly standard for future development in this repository before adding new platform scripts.

## Assessment summary of current repository

### Structure and usage patterns
- Repository is organized by domain (`applications`, `databases`, `os`, `sampling`) but implementation style is highly mixed.
- Some tools are packaged and orchestrated (GitHub audit), while others are single-file ad hoc scripts.
- Output behavior varies: terminal-only, local flat files, custom timestamp folders, or no persisted evidence.

### Dependencies and runtime
- Global dependencies are minimal (`pandas`, `requests`, `dash`, `plotly`) and not tied to per-tool requirements.
- Several shell tools require external binaries (`aws`, `jq`, `netstat`, distro-specific commands) but these are inconsistently documented.

### Naming and documentation patterns
- Script names are mostly descriptive but not consistently scoped by control objective.
- README depth varies significantly by domain.
- Root README contains a typo in clone URL and is Org format, while subdocs are mostly Markdown.

### Authentication handling
- GitHub uses env/config pattern (good baseline).
- Multiple GitLab scripts hardcode token placeholders in source (must be remediated before extension).
- AWS scripts rely on ambient CLI auth (acceptable if explicitly documented).

### Output/evidence consistency
- GitHub has strongest structure (timestamped output folder + summary).
- AWS/Linux scripts generate varying flat report files and mixed JSON/text.
- No common metadata manifest across tools.
- No standard separation of raw evidence vs parsed evidence vs exceptions.

## Inconsistencies identified
1. CLI argument sets differ (or are absent).
2. Output roots and naming are inconsistent.
3. Data schemas vary without documented contracts.
4. Error handling ranges from silent fallback to immediate exit without normalized exception records.
5. Authentication practices are inconsistent and sometimes insecure.
6. No unified test or lint strategy.

## Target standards (authoritative references)
- Repository structure: `docs/repository-structure.md`
- Script behavior + CLI + error/logging: `docs/script-standards.md`
- Output/model/schema + metadata: `docs/output-standards.md`
- Root/per-tool documentation templates: `docs/documentation-standards.md`
- Delivery sequence and risks: `docs/migration-plan.md`

## Proposed standard script template (minimal)
1. Parse standard args.
2. Validate scope, auth, and prerequisites.
3. Create deterministic run directory.
4. Collect raw data (non-destructive).
5. Transform to parsed normalized datasets.
6. Write exceptions and metadata.
7. Write logs and concise auditor summary.
8. Return standard exit code.

## Before/after examples

### Example A: GitLab flat script
- **Before**: token in code, prints to terminal, no output package.
- **After**: env/config auth, writes standard output tree, includes `metadata.json`, parsed CSV/JSON, and exception records.

### Example B: Linux shell report
- **Before**: single `report.txt`, mixed command/file output.
- **After**: raw command captures in `raw/`, normalized checks in `parsed/`, failed commands in `exceptions/`, plus run log and metadata.

## Dependency and quality strategy
- Short term: retain `requirements.txt` for compatibility.
- Medium term: introduce `pyproject.toml` for tooling and consistent dev setup.
- Add lint/format baselines (`ruff` + `black` for Python, `shellcheck` + `shfmt` for shell).
- Add minimal test harness with smoke tests for all CLI entrypoints.

## Security and defensibility guidance
- Never write credentials to outputs/logs.
- Minimize privileges and document required scopes.
- Keep raw evidence immutable per run.
- Ensure chain of custody via metadata (`who`, `when`, `scope`, `command`, `tool version`).
- Log what was not collected and why.

## Phased execution plan (for follow-up commits)
- Execute phases exactly as documented in `docs/migration-plan.md`.
- Prioritize credential-remediation and output normalization before adding new scripts.

## Concise checklist for next implementation pass
- [ ] Add shared CLI/output/metadata utilities.
- [ ] Migrate GitLab scripts off hardcoded credential patterns.
- [ ] Implement standard output tree for GitHub/AWS/Linux tools.
- [ ] Add `metadata.json` emission to every run.
- [ ] Normalize README structure at root and per-tool levels.
- [ ] Add tests (CLI smoke + parser unit tests).
- [ ] Add lint/format tooling and CI enforcement.
- [ ] Preserve backward compatibility notes for legacy output paths.
