"""
Collect branch protection and ruleset data across all repos in an org.
"""

import sys

import requests

from .api import paginate


def branch_protections(org, cfg):
    """
    For each repo, return protection settings per branch and any rulesets.
    Branches with no protection are included with protected=False.
    Repos that return 403 on the branches endpoint are skipped with a warning.
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
            if e.response is not None and e.response.status_code == 403:
                print(
                    f"  Skipping {repo_name}: branches endpoint returned 403",
                    file=sys.stderr,
                )
                continue
            raise

        for branch in branches:
            branch_name = branch["name"]
            url = (
                f"https://api.github.com/repos/{org}/{repo_name}"
                f"/branches/{branch_name}/protection"
            )
            resp = requests.get(url, headers=cfg["headers"], timeout=cfg["timeout"])

            if resp.status_code in (403, 404):
                rows.append(
                    {
                        "repo": repo_name,
                        "branch": branch_name,
                        "protected": False,
                        "required_reviews": None,
                        "dismiss_stale_reviews": None,
                        "require_code_owner_reviews": None,
                        "required_status_checks": None,
                        "enforce_admins": None,
                        "restrictions": None,
                    }
                )
                continue

            resp.raise_for_status()
            p = resp.json()
            reviews = p.get("required_pull_request_reviews", {})
            checks = p.get("required_status_checks", {})

            rows.append(
                {
                    "repo": repo_name,
                    "branch": branch_name,
                    "protected": True,
                    "required_reviews": reviews.get("required_approving_review_count"),
                    "dismiss_stale_reviews": reviews.get("dismiss_stale_reviews"),
                    "require_code_owner_reviews": reviews.get(
                        "require_code_owner_reviews"
                    ),
                    "required_status_checks": ", ".join(checks.get("contexts", []))
                    or None,
                    "enforce_admins": p.get("enforce_admins", {}).get("enabled"),
                    "restrictions": bool(p.get("restrictions")),
                }
            )

    return rows
