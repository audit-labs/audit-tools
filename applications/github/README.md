> **NOTE**: The PAT used across all scripts needs the following minimum permissions:
> - Repository: Actions (read), Contents (read), Metadata (read), Workflows (read)
> - Organization: Administration (read), Members (read)
> - Audit log collection also requires GitHub Enterprise Cloud. Classic PATs need
>   `read:audit_log`; fine-grained tokens need Organization Administration (read).

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
| `audit_log.csv` | Branch protection and repository ruleset audit-log changes from the last 180 days (Enterprise Cloud only) |
| `summary.txt` | Row counts per section |

`audit_log.csv` is collected by default. GitHub only returns audit-log events
from the past three months unless the query includes a date filter, so this
tool filters with `created:>=<180-days-ago>` to cover GitHub's 180-day audit-log
retention window for non-Git events. If the organization or token cannot access
the audit log, the tool prints a warning and continues with the other evidence.
