# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `sampling_tool.engine`: one standard-library selection algorithm (random, systematic, stratified) seeded from strings, so a seed selects the same rows with or without pandas and on every install. Sample manifests record `engine` and `engine_version` (2). `audit-sample --method systematic`.
- Attribute sample sizes and upper deviation limits from the binomial distribution, matching the AICPA Audit Sampling guide tables for large populations; default sample sizes by control frequency.

### Changed

- `random_sample` and `stratified_sample` select through the engine. The same seed now selects different rows than version 1 did; earlier runs remain verifiable from their saved outputs.

- Installable package: `pip install audit-tools` installs `tui`, `applications`,
  and `sampling` as packages, the `audit-sample` and `audit-tui` commands, and the
  SQL/OS procedure library and sampling examples under `<prefix>/share/audit-tools/`.

## [1.0.0] - 2026-08-07

First tagged release. Prior work was untagged; this marks the collection as stable
and gives engagements an exact revision to pin to.

### Added

- Interactive terminal UI (`audit_tui.py`) that runs audits against GitHub,
  GitLab, and AWS — pick a platform, enter connection details, choose checks, and
  watch live progress.
- Evidence collectors and security-posture checks for GitHub (branch protection
  and rulesets, audit log), GitLab, and AWS (account, network, logging, password
  policy, S3).
- Database access collectors (MySQL, Postgres, MongoDB) and OS-level checks.
- Reproducible audit sampling CLI plus a standalone HTML sampling tool.
- Dependency extras (`analysis`, `dashboards`, `aws`, `collectors`, `mongo`,
  `tui`, `all`, `dev`) so a locked-down auditing laptop installs only what a
  procedure needs.
- CodeQL and Ruff CI.

[1.0.0]: https://github.com/audit-labs/audit-tools/releases/tag/v1.0.0
