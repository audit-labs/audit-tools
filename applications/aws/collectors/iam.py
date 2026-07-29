"""
Collect IAM user hygiene and the account password policy.
"""

import sys
from datetime import datetime, timezone

from botocore.exceptions import ClientError


def iam_users(cfg):
    """
    One row per IAM user: MFA status, access-key count and oldest key age,
    whether a console password is set, and last password use.
    """
    iam = cfg["session"].client("iam")
    now = datetime.now(timezone.utc)
    rows = []

    for page in iam.get_paginator("list_users").paginate():
        for u in page["Users"]:
            name = u["UserName"]
            mfa = iam.list_mfa_devices(UserName=name).get("MFADevices", [])
            keys = iam.list_access_keys(UserName=name).get("AccessKeyMetadata", [])
            key_ages = [(now - k["CreateDate"]).days for k in keys]

            try:
                iam.get_login_profile(UserName=name)
                console = True
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchEntity":
                    console = False
                else:
                    raise

            last_used = u.get("PasswordLastUsed")
            rows.append(
                {
                    "user": name,
                    "mfa_enabled": bool(mfa),
                    "access_keys": len(keys),
                    "oldest_key_age_days": max(key_ages) if key_ages else "",
                    "console_password": console,
                    "password_last_used": last_used.isoformat() if last_used else "",
                    "created": u["CreateDate"].isoformat()
                    if u.get("CreateDate")
                    else "",
                }
            )
    return rows


def password_policy(cfg):
    """
    One row describing the account IAM password policy. Returns an empty list
    with a warning if no policy is set.
    """
    iam = cfg["session"].client("iam")
    try:
        p = iam.get_account_password_policy()["PasswordPolicy"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            print(
                "Warning: no IAM password policy is set for this account -- skipping.",
                file=sys.stderr,
            )
            return []
        raise

    return [
        {
            "minimum_length": p.get("MinimumPasswordLength"),
            "require_symbols": p.get("RequireSymbols"),
            "require_numbers": p.get("RequireNumbers"),
            "require_uppercase": p.get("RequireUppercaseCharacters"),
            "require_lowercase": p.get("RequireLowercaseCharacters"),
            "allow_users_to_change": p.get("AllowUsersToChangePassword"),
            "max_age_days": p.get("MaxPasswordAge", "N/A"),
            "reuse_prevention": p.get("PasswordReusePrevention", "N/A"),
            "hard_expiry": p.get("HardExpiry", False),
        }
    ]
