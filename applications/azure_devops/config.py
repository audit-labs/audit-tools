"""
Configuration loader for the Azure DevOps audit tool.

Reads AZDO_ORG, AZDO_PAT, and (optionally) AZDO_URL from the environment. The
PAT is read from the environment only — never passed on the command line.

Usage:
    export AZDO_ORG=my-org
    export AZDO_PAT=your_pat          # read scopes
    export AZDO_URL=https://azuredevops.example.com/DefaultCollection  # Server
"""

import os
import sys

from collectors.api import DEFAULT_BASE_URL, build_cfg


def load(org_override=None, base_url_override=None):
    """Return a config dict. Exits with an error if required values are missing."""
    pat = os.environ.get("AZDO_PAT", "").strip()
    org = org_override or os.environ.get("AZDO_ORG", "").strip()
    base_url = (
        base_url_override or os.environ.get("AZDO_URL", "").strip() or DEFAULT_BASE_URL
    )

    missing = []
    if not pat:
        missing.append("AZDO_PAT")
    if not org:
        missing.append("AZDO_ORG (or pass --org)")

    if missing:
        print(f"Error: missing required values: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    return build_cfg(org, pat, base_url)
