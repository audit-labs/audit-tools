> **NOTE**: Authentication uses a Personal Access Token sent as HTTP Basic. Use
> a **read-only** PAT. Scopes needed across the checks:
> - Project and Team (read), Code (read) — projects, repositories, branch policies
> - Member Entitlement Management (read) — user entitlements
> - Graph (read) — group memberships
> - Service Connections (read) — service connections
>
> The PAT is read from `AZDO_PAT` (environment only, never a command-line flag).
> Checks that a PAT can't reach are skipped with a warning; the rest still run.

---

# `audit.py` — Unified Azure DevOps Audit Tool

Runs all collectors against an Azure DevOps organization and writes a
timestamped audit package to disk. This is the tool the interactive TUI
(`audit_tui.py`) drives.

## Setup

```bash
export AZDO_ORG=my-org
export AZDO_PAT=your_pat
# Azure DevOps Server (on-prem) only:
export AZDO_URL=https://azuredevops.example.com/DefaultCollection
```

## Usage

```bash
# Basic run — uses AZDO_ORG and AZDO_PAT from environment
python audit.py

# Override org, set output directory
python audit.py --org my-org --out ./output

# Point at an Azure DevOps Server collection
python audit.py --url https://azuredevops.example.com/DefaultCollection
```

## Output

Creates a directory: `<out>/azure_devops_audit_<org>_<YYYY-MM-DD>/`

| File | Contents |
|---|---|
| `projects.csv` | All projects with visibility and state |
| `user_entitlements.csv` | Org members with access level (license) and last access |
| `group_memberships.csv` | Members of each org security group (names resolved) |
| `repositories.csv` | Repositories per project with default branch |
| `branch_policies.csv` | Branch policies per project (required reviewers, build validation, …) |
| `service_connections.csv` | Pipeline service connections per project (type, shared, auth scheme) |
| `summary.txt` | Row counts per section |

Branch policies are Azure DevOps' equivalent of branch protection. Service
connections hold pipeline credentials — over-shared ones are a common finding.

The API spans a few hostnames (`dev.azure.com`, `vsaex.dev.azure.com`,
`vssps.dev.azure.com`) derived from the org; this targets Azure DevOps Services,
and Azure DevOps Server is best-effort via `--url`.
