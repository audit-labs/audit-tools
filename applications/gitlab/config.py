"""
Configuration loader for the GitLab audit tool.

Reads GITLAB_TOKEN, GITLAB_GROUP, and (optionally) GITLAB_URL from the
environment.

Usage:
    export GITLAB_TOKEN=your_token
    export GITLAB_GROUP=your_group_id_or_path
    export GITLAB_URL=https://gitlab.example.com/api/v4   # self-hosted only
"""

import os
import sys

from collectors.api import DEFAULT_BASE_URL


def load(group_override=None, base_url_override=None):
    """Return a config dict. Exits with an error if required values are missing."""
    token = os.environ.get("GITLAB_TOKEN", "").strip()
    group = group_override or os.environ.get("GITLAB_GROUP", "").strip()
    base_url = (
        base_url_override
        or os.environ.get("GITLAB_URL", "").strip()
        or DEFAULT_BASE_URL
    )

    missing = []
    if not token:
        missing.append("GITLAB_TOKEN")
    if not group:
        missing.append("GITLAB_GROUP (or pass --group)")

    if missing:
        print(f"Error: missing required values: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    return {
        "token": token,
        "group": group,
        "base_url": base_url.rstrip("/"),
        "headers": {"PRIVATE-TOKEN": token},
        "timeout": 30,
    }
