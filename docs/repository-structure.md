# Repository Structure Assessment and Target Model

## Current structure (as of 2026-04-29)

```text
.
├── applications/
│   ├── aws/
│   ├── github/
│   └── gitlab/
├── databases/
│   ├── mongo/
│   ├── mysql/
│   ├── oracle/
│   ├── postgres/
│   └── sql/
├── os/
│   ├── linux/
│   └── windows/
├── project_management/
├── sampling/
├── README.org
└── requirements.txt
```

### Observed categories
- **Platform/API scripts**: `applications/*` (AWS, GitHub, GitLab).
- **Database evidence queries/scripts**: `databases/*` (mixed SQL and Python).
- **Host/OS evidence scripts**: `os/linux/*`.
- **Sampling utilities**: `sampling/*`.
- **Non-collection artifacts**: `project_management/*` (dashboards/workbooks).

## Key structural inconsistencies
1. **Mixed script placement patterns**: some tools have subpackages (`applications/github/collectors`), others are flat files.
2. **No cross-repo standard output root**: scripts write to `./output`, current directory, or terminal only.
3. **No common `docs/` model** for per-tool audit purpose, control mapping, or schema.
4. **Mixed README formats**: root uses `README.org`, most subareas use markdown.
5. **No `tests/` structure** for any script family.

## Proposed target repository layout

```text
.
├── tools/
│   ├── applications/
│   │   ├── aws/
│   │   │   ├── iam_assignments/
│   │   │   ├── password_policy/
│   │   │   └── s3_public_access/
│   │   ├── github/
│   │   │   └── org_audit/
│   │   └── gitlab/
│   │       ├── approvals/
│   │       ├── branch_protections/
│   │       └── ...
│   ├── databases/
│   ├── os/
│   └── sampling/
├── docs/
│   ├── repository-structure.md
│   ├── script-standards.md
│   ├── output-standards.md
│   ├── documentation-standards.md
│   ├── migration-plan.md
│   └── standardization-plan.md
├── outputs/                      # gitignored runtime evidence root
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml                # Python dependency + lint config
├── requirements.txt              # optional lock/export for compatibility
└── README.md
```

## Practical adoption notes (non-breaking)
- Keep existing folders temporarily; add `tools/` gradually and migrate scripts in phases.
- If immediate relocation is too disruptive, keep current paths but enforce standards first.
- Standardize script behavior/output before moving every file.

## Files likely needing future structural changes
- Root documentation: `README.org` → future canonical `README.md`.
- Flat GitLab scripts under `applications/gitlab/*.py` into per-tool directories.
- Shell scripts writing local reports (`applications/aws/*.sh`, `os/linux/*.sh`) to standard `outputs/<tool>/<run_id>/...`.
- Add missing top-level `tests/`, `outputs/.gitkeep`, and `.gitignore` rules.
