"""
Collect repositories and branch policies for every project.

Branch policies are Azure DevOps' equivalent of branch protection: required
reviewers, build validation, comment resolution, etc., scoped to branches.
"""

from .api import core_url, safe_paginate

API_VERSION = "7.1"


def repositories(cfg, projects):
    rows = []
    for p in projects:
        repos = safe_paginate(
            core_url(cfg, f"{p['id']}/_apis/git/repositories"),
            cfg,
            {"api-version": API_VERSION},
            f"{p.get('name', p['id'])} repositories",
        )
        for r in repos:
            rows.append(
                {
                    "project": p.get("name", ""),
                    "repo": r.get("name", ""),
                    "default_branch": r.get("defaultBranch", "") or "(none)",
                    "is_disabled": r.get("isDisabled", False),
                    "size_bytes": r.get("size", ""),
                    "web_url": r.get("webUrl", ""),
                }
            )
    return rows


def branch_policies(cfg, projects):
    rows = []
    for p in projects:
        configs = safe_paginate(
            core_url(cfg, f"{p['id']}/_apis/policy/configurations"),
            cfg,
            {"api-version": API_VERSION},
            f"{p.get('name', p['id'])} policies",
        )
        for c in configs:
            settings = c.get("settings", {})
            scopes = settings.get("scope", [])
            rows.append(
                {
                    "project": p.get("name", ""),
                    "policy_type": c.get("type", {}).get("displayName", ""),
                    "enabled": c.get("isEnabled"),
                    "blocking": c.get("isBlocking"),
                    "min_reviewers": settings.get("minimumApproverCount", ""),
                    "scope": ", ".join(s.get("refName", "") for s in scopes)
                    or "(all branches)",
                }
            )
    return rows
