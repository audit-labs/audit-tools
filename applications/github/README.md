> **NOTE**: The PAT used across all scripts needs the following minimum permissions:
> - Repository: Actions (read), Contents (read), Metadata (read), Workflows (read)
> - Organization: Administration (read), Members (read)

---

# `audit.py` — Unified GitHub Audit Tool

Runs all collectors against a GitHub organization and writes a timestamped
audit package to disk.

## Setup

```bash
export GITHUB_TOKEN=your_token
export GITHUB_ORG=your_organization
```

## Usage

```bash
# Basic run — uses GITHUB_TOKEN and GITHUB_ORG from environment
python audit.py

# Override org, set output directory
python audit.py --org my-org --out ./output

# Collect commits from a non-default branch
python audit.py --branch develop

# Include audit log (requires GitHub Enterprise)
python audit.py --include-audit-log
```

## Output

Creates a directory: `<out>/github_audit_<org>_<YYYY-MM-DD>/`

| File | Contents |
|---|---|
| `member_roster.csv` | All org members with role (owner vs member) |
| `two_factor_disabled.csv` | Org members without 2FA enabled |
| `outside_collaborators.csv` | Non-org members with direct repo access |
| `privileged_access.csv` | All users with admin permission on any repo |
| `pending_invitations.csv` | Invitations not yet accepted, with age in days |
| `team_permissions.csv` | Teams, their repos, permissions, and members |
| `permission_matrix.csv` | Full user/repo/permission cross-reference |
| `branch_protections.csv` | Branch protection settings across all repos |
| `commits.csv` | Commit history across all repos for the target branch |
| `audit_log.csv` | Org-level audit events (Enterprise only, opt-in) |
| `summary.txt` | Row counts per section |


