"""
Collect branch protection across all repos in an org.

Protection can come from two independent systems:

- **Classic branch protection** (``/branches/{branch}/protection``)
- **Rulesets** (org- or repo-level) — a branch protected only by a ruleset does
  not appear in the classic endpoint at all.

Both are checked per branch and merged, so ruleset-only protection is no longer
reported as unprotected. ``protection_source`` records where the protection
comes from.
"""

import sys

import requests

from .api import paginate

_NO_PROTECTION = {
    "required_reviews": None,
    "dismiss_stale_reviews": None,
    "require_code_owner_reviews": None,
    "required_status_checks": None,
    "enforce_admins": None,
    "restrictions": None,
}


def branch_protections(org, cfg):
    """For each repo, return protection settings per branch (classic + ruleset).

    Repos whose branches endpoint returns 403/404 are skipped with a warning.
    """
    repos = paginate(f"https://api.github.com/orgs/{org}/repos", cfg)
    rows = []

    for repo in repos:
        repo_name = repo["name"]
        try:
            branches = paginate(
                f"https://api.github.com/repos/{org}/{repo_name}/branches", cfg
            )
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                print(
                    f"  Skipping {repo_name}: branches endpoint returned "
                    f"{e.response.status_code}",
                    file=sys.stderr,
                )
                continue
            raise

        for branch in branches:
            rows.append(_branch_row(org, repo_name, branch["name"], cfg))

    return rows


def _branch_row(org, repo, branch, cfg):
    classic = _classic_protection(org, repo, branch, cfg)
    ruleset = _ruleset_protection(org, repo, branch, cfg)

    if classic and ruleset:
        source = "branch protection + ruleset"
    elif classic:
        source = "branch protection"
    elif ruleset:
        source = "ruleset"
    else:
        source = ""

    # Prefer classic values where present, otherwise fall back to ruleset.
    details = classic or ruleset or _NO_PROTECTION
    return {
        "repo": repo,
        "branch": branch,
        "protected": bool(classic or ruleset),
        "protection_source": source,
        **details,
    }


def _classic_protection(org, repo, branch, cfg):
    """Return classic branch-protection details, or None if not protected."""
    url = f"https://api.github.com/repos/{org}/{repo}/branches/{branch}/protection"
    resp = requests.get(url, headers=cfg["headers"], timeout=cfg["timeout"])
    if resp.status_code in (403, 404):
        return None
    resp.raise_for_status()
    p = resp.json()
    reviews = p.get("required_pull_request_reviews", {})
    checks = p.get("required_status_checks", {})
    return {
        "required_reviews": reviews.get("required_approving_review_count"),
        "dismiss_stale_reviews": reviews.get("dismiss_stale_reviews"),
        "require_code_owner_reviews": reviews.get("require_code_owner_reviews"),
        "required_status_checks": ", ".join(checks.get("contexts", [])) or None,
        "enforce_admins": p.get("enforce_admins", {}).get("enabled"),
        "restrictions": bool(p.get("restrictions")),
    }


def _ruleset_protection(org, repo, branch, cfg):
    """Return protection derived from the rulesets active on a branch, or None.

    The per-branch rules endpoint aggregates the rules enforced on the branch
    from every applicable org- and repo-level ruleset.
    """
    url = f"https://api.github.com/repos/{org}/{repo}/rules/branches/{branch}"
    try:
        rules = paginate(url, cfg)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            return None
        raise
    if not rules:
        return None

    params = {}
    for rule in rules:
        params.setdefault(rule.get("type"), rule.get("parameters") or {})

    pull_request = params.get("pull_request", {})
    status_checks = params.get("required_status_checks", {})
    contexts = [
        c.get("context", "") for c in status_checks.get("required_status_checks", [])
    ]
    return {
        "required_reviews": pull_request.get("required_approving_review_count"),
        "dismiss_stale_reviews": pull_request.get("dismiss_stale_reviews_on_push"),
        "require_code_owner_reviews": pull_request.get("require_code_owner_review"),
        "required_status_checks": ", ".join(contexts) or None,
        # Rulesets model admin enforcement and push restrictions via bypass
        # actors, which the per-branch rules endpoint does not return.
        "enforce_admins": None,
        "restrictions": None,
    }
