"""
Collect open secret-scanning and Dependabot alerts across the organization.

Both require GitHub Advanced Security (or public repos) and admin access. If the
org or token can't reach them, the collector returns an empty list with a
warning instead of failing the run.
"""

import sys

import requests

from .api import paginate


def secret_scanning(org, cfg):
    return _org_alerts(org, cfg, "secret-scanning", _secret_row, "secret scanning")


def dependabot_alerts(org, cfg):
    return _org_alerts(org, cfg, "dependabot", _dependabot_row, "Dependabot")


def _org_alerts(org, cfg, kind, row_fn, label):
    try:
        alerts = paginate(
            f"https://api.github.com/orgs/{org}/{kind}/alerts", cfg, {"state": "open"}
        )
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            print(
                f"Warning: {label} alerts require GitHub Advanced Security and "
                "org admin access -- skipping.",
                file=sys.stderr,
            )
            return []
        raise
    return [row_fn(a) for a in alerts]


def _secret_row(alert):
    return {
        "repo": alert.get("repository", {}).get("full_name", ""),
        "secret_type": alert.get("secret_type_display_name")
        or alert.get("secret_type", ""),
        "state": alert.get("state", ""),
        "created_at": alert.get("created_at", ""),
        "html_url": alert.get("html_url", ""),
    }


def _dependabot_row(alert):
    dependency = alert.get("dependency", {})
    advisory = alert.get("security_advisory", {})
    return {
        "repo": alert.get("repository", {}).get("full_name", ""),
        "package": dependency.get("package", {}).get("name", ""),
        "severity": advisory.get("severity", ""),
        "summary": advisory.get("summary", ""),
        "state": alert.get("state", ""),
        "created_at": alert.get("created_at", ""),
        "html_url": alert.get("html_url", ""),
    }
