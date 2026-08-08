# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
