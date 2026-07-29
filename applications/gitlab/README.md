> **NOTE**: The token used across all collectors needs at least the `read_api`
> scope. Some checks need more:
> - **Approval rules** and **audit events** require a GitLab Premium or Ultimate
>   subscription.
> - **Password policy** reads instance application settings, which require an
>   admin token on a self-hosted instance (not available on GitLab.com).
>
> Checks that are unavailable are skipped with a warning; the rest still run.

---

# `audit.py` — Unified GitLab Audit Tool

Runs all collectors against a GitLab group (including its subgroups) and writes
a timestamped audit package to disk.

## Setup

```bash
export GITLAB_TOKEN=your_token
export GITLAB_GROUP=your_group_id_or_path
# Self-hosted only:
export GITLAB_URL=https://gitlab.example.com/api/v4
```

## Usage

```bash
# Basic run — uses GITLAB_TOKEN and GITLAB_GROUP from environment
python audit.py

# Override group, set output directory
python audit.py --group my-group --out ./output

# Point at a self-hosted instance
python audit.py --url https://gitlab.example.com/api/v4
```

The group may be a numeric ID (`1234567`) or a URL path (`my-group/sub-group`).

## Output

Creates a directory: `<out>/gitlab_audit_<group>_<YYYY-MM-DD>/`

| File | Contents |
|---|---|
| `group_members.csv` | Group members with access level and role |
| `projects.csv` | All projects in the group and subgroups |
| `project_members.csv` | Members and access levels for every project |
| `branch_protections.csv` | Protected-branch settings across all projects |
| `pipelines.csv` | CI/CD pipeline history across all projects |
| `approval_rules.csv` | Merge-request approval rules (Premium/Ultimate) |
| `audit_events.csv` | Group membership audit events (Premium/Ultimate) |
| `password_policy.csv` | Instance password policy (self-hosted, admin token) |
| `summary.txt` | Row counts per section |

The per-project checks reuse a single enumeration of the group's projects, so
the group is listed only once per run.
