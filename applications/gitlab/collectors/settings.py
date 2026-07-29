"""
Collect the instance password policy from application settings.

Requires an admin token on a self-hosted instance; not available on
GitLab.com. Returns an empty list with a warning on 403/404.
"""

import sys

import requests

PASSWORD_FIELDS = [
    "minimum_password_length",
    "password_number_required",
    "password_symbol_required",
    "password_uppercase_required",
    "password_lowercase_required",
]


def password_policy(group, cfg):
    """group is unused; application settings are instance-wide."""
    url = f"{cfg['base_url']}/application/settings"
    try:
        resp = requests.get(url, headers=cfg["headers"], timeout=cfg["timeout"])
        resp.raise_for_status()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            print(
                "Warning: application settings require an admin token on a "
                "self-hosted instance -- skipping.",
                file=sys.stderr,
            )
            return []
        raise

    settings = resp.json()
    return [{field: settings.get(field, "Not set") for field in PASSWORD_FIELDS}]
