"""
Configuration loader for the AWS audit tool.

Reads AWS_PROFILE, AWS_DEFAULT_REGION, and AWS_AUDIT_ACCOUNT from the
environment. Credentials themselves come from the standard boto3 credential
chain — this tool never handles access keys directly.

Usage:
    export AWS_PROFILE=my-profile          # optional; else default chain
    export AWS_DEFAULT_REGION=us-east-1    # optional
    export AWS_AUDIT_ACCOUNT=my-account    # optional; only for SSO assignments
"""

import os

from collectors.api import build_cfg


def load(profile_override=None, region_override=None, account_override=None):
    """Return a config dict. AWS needs no required token to validate here;
    missing or invalid credentials surface at call time."""
    profile = profile_override or os.environ.get("AWS_PROFILE", "").strip()
    region = region_override or os.environ.get("AWS_DEFAULT_REGION", "").strip()
    account = account_override or os.environ.get("AWS_AUDIT_ACCOUNT", "").strip()
    return build_cfg(profile, region, account)
