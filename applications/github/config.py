"""
Configuration loader for the GitHub audit tool.

Reads GITHUB_TOKEN and GITHUB_ORG from environment variables.

Usage:
    export GITHUB_TOKEN=your_token
    export GITHUB_ORG=your_organization
"""

import os
import sys


def load(org_override=None):
    """
    Return a config dict. Exits with an error if required values are missing.
    """
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    org = org_override or os.environ.get("GITHUB_ORG", "").strip()

    missing = []
    if not token:
        missing.append("GITHUB_TOKEN")
    if not org:
        missing.append("GITHUB_ORG (or pass --org)")

    if missing:
        print(f"Error: missing required values: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    return {
        "token": token,
        "org": org,
        "headers": {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        "timeout": 30,
    }
