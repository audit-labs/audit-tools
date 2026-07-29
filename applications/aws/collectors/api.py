"""Shared AWS session helpers.

Authentication uses the standard boto3 credential chain (environment variables,
shared config/credentials files, SSO profiles, instance roles). No access keys
are ever passed in or stored by this tool.
"""

import boto3


def build_cfg(profile="", region="", account=""):
    """Build the config dict the collectors expect.

    ``profile`` and ``region`` are optional; when empty, boto3's default
    resolution applies. ``account`` is an optional account name used only by the
    SSO assignments collector.
    """
    kwargs = {}
    if profile:
        kwargs["profile_name"] = profile
    if region:
        kwargs["region_name"] = region
    session = boto3.Session(**kwargs)
    return {
        "session": session,
        "profile": profile,
        "region": region,
        "account": account,
    }


def account_id(cfg):
    """Return the AWS account ID for the active credentials, or '' on failure."""
    try:
        return cfg["session"].client("sts").get_caller_identity()["Account"]
    except Exception:
        return ""


def enabled_regions(cfg):
    """Return the region names enabled for the account (for region-scoped checks)."""
    ec2 = cfg["session"].client("ec2", region_name=cfg.get("region") or "us-east-1")
    return [r["RegionName"] for r in ec2.describe_regions().get("Regions", [])]
