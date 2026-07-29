"""
Collect organization-level security settings.

Reads the org object; several fields are only populated when the token has org
admin access.
"""

import requests


def org_security(org, cfg):
    resp = requests.get(
        f"https://api.github.com/orgs/{org}",
        headers=cfg["headers"],
        timeout=cfg["timeout"],
    )
    resp.raise_for_status()
    o = resp.json()
    return [
        {
            "org": org,
            "two_factor_required": o.get("two_factor_requirement_enabled"),
            "default_repo_permission": o.get("default_repository_permission"),
            "members_can_create_repos": o.get("members_can_create_repositories"),
            "members_can_create_public_repos": o.get(
                "members_can_create_public_repositories"
            ),
            "members_can_create_pages": o.get("members_can_create_pages"),
            "web_commit_signoff_required": o.get("web_commit_signoff_required"),
            "advanced_security_for_new_repos": o.get(
                "advanced_security_enabled_for_new_repositories"
            ),
            "secret_scanning_for_new_repos": o.get(
                "secret_scanning_enabled_for_new_repositories"
            ),
            "secret_scanning_push_protection_for_new_repos": o.get(
                "secret_scanning_push_protection_enabled_for_new_repositories"
            ),
        }
    ]
