"""
Collect org membership, access, and permission data.

Covers:
- Org member roster with roles (owner vs member)
- Outside collaborators
- Privileged access (admin permission on any repo)
- Pending org invitations
- Team memberships and repo permissions
- Full per-repo permission matrix
- Members with 2FA disabled
"""

import sys
from datetime import datetime, timezone

import requests

from .api import paginate


def _permission_level(perms):
    for level in ("admin", "maintain", "push", "triage", "pull"):
        if perms.get(level):
            return "write" if level == "push" else level
    return "unknown"


def _repos(org, cfg):
    return paginate(f"https://api.github.com/orgs/{org}/repos", cfg)


def fetch_repo_collaborators(org, cfg):
    """
    Fetch collaborators for every repo once (affiliation=all).
    Returns a list of dicts: {repo, visibility, collaborators}.
    Repos that 403 are skipped with a warning.
    This cache is passed into outside_collaborators, privileged_access,
    and permission_matrix to avoid redundant API calls.
    """
    repos = _repos(org, cfg)
    results = []
    for repo in repos:
        repo_name = repo["name"]
        try:
            collabs = paginate(
                f"https://api.github.com/repos/{org}/{repo_name}/collaborators",
                cfg,
                {"affiliation": "all"},
            )
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 403:
                print(f"  Skipping {repo_name}: collaborators endpoint returned 403", file=sys.stderr)
                continue
            raise
        results.append({
            "repo": repo_name,
            "visibility": repo["visibility"],
            "collaborators": collabs,
        })
    return results


def member_roster(org, cfg):
    members = paginate(f"https://api.github.com/orgs/{org}/members", cfg, {"role": "all"})
    owners = {
        m["login"]
        for m in paginate(f"https://api.github.com/orgs/{org}/members", cfg, {"role": "owner"})
    }
    return [
        {
            "login": m["login"],
            "org_role": "owner" if m["login"] in owners else "member",
            "profile_url": m["html_url"],
        }
        for m in members
    ]


def two_factor_disabled(org, cfg):
    """
    List org members who do not have 2FA enabled.
    Requires the token to have read:org scope.
    Note: GitHub only exposes this to org owners.
    """
    members = paginate(
        f"https://api.github.com/orgs/{org}/members",
        cfg,
        {"filter": "2fa_disabled"},
    )
    return [
        {
            "login": m["login"],
            "profile_url": m["html_url"],
        }
        for m in members
    ]


def outside_collaborators(org, cfg, repo_collabs):
    """
    Non-org members with direct repo access.
    Accepts pre-fetched repo_collabs from fetch_repo_collaborators().
    """
    outside = {
        m["login"]
        for m in paginate(f"https://api.github.com/orgs/{org}/outside_collaborators", cfg)
    }
    rows = []
    for entry in repo_collabs:
        for c in entry["collaborators"]:
            if c["login"] in outside:
                rows.append({
                    "login": c["login"],
                    "repo": entry["repo"],
                    "permission": _permission_level(c.get("permissions", {})),
                    "repo_visibility": entry["visibility"],
                })
    return rows


def privileged_access(org, cfg, repo_collabs):
    """
    All users with admin permission on any repo.
    Accepts pre-fetched repo_collabs from fetch_repo_collaborators().
    """
    rows = []
    for entry in repo_collabs:
        for c in entry["collaborators"]:
            if c.get("permissions", {}).get("admin"):
                rows.append({
                    "login": c["login"],
                    "repo": entry["repo"],
                    "permission": "admin",
                    "repo_visibility": entry["visibility"],
                })
    return rows


def pending_invitations(org, cfg):
    now = datetime.now(timezone.utc)
    rows = []
    for inv in paginate(f"https://api.github.com/orgs/{org}/invitations", cfg):
        created = inv.get("created_at", "")
        age_days = None
        if created:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            age_days = (now - dt).days
        rows.append({
            "login": inv.get("login") or inv.get("email", "unknown"),
            "role": inv.get("role", ""),
            "invited_by": inv.get("inviter", {}).get("login", ""),
            "created_at": created,
            "age_days": age_days,
        })
    return rows


def team_permissions(org, cfg):
    rows = []
    for team in paginate(f"https://api.github.com/orgs/{org}/teams", cfg):
        slug = team["slug"]
        team_members = paginate(f"https://api.github.com/orgs/{org}/teams/{slug}/members", cfg)
        team_repos = paginate(f"https://api.github.com/orgs/{org}/teams/{slug}/repos", cfg)
        member_logins = ", ".join(m["login"] for m in team_members) or "(none)"
        for repo in team_repos:
            rows.append({
                "team": team["name"],
                "repo": repo["name"],
                "permission": _permission_level(repo.get("permissions", {})),
                "members": member_logins,
            })
    return rows


def permission_matrix(org, cfg, repo_collabs):
    """
    Full per-repo/per-user permission cross-reference.
    Accepts pre-fetched repo_collabs from fetch_repo_collaborators().
    """
    rows = []
    for entry in repo_collabs:
        for c in entry["collaborators"]:
            rows.append({
                "repo": entry["repo"],
                "login": c["login"],
                "permission": _permission_level(c.get("permissions", {})),
                "visibility": entry["visibility"],
            })
    return rows
