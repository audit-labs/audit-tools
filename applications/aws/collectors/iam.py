"""
Collect IAM user hygiene, the account password policy, and account-level
security summary (root MFA, root access keys).
"""

import sys
from datetime import datetime, timezone

from botocore.exceptions import ClientError


def account_security(cfg):
    """
    One row of account-level security signals from the IAM account summary:
    whether the root user has MFA and access keys, plus resource counts.
    """
    iam = cfg["session"].client("iam")
    s = iam.get_account_summary()["SummaryMap"]
    return [
        {
            "root_mfa_enabled": bool(s.get("AccountMFAEnabled", 0)),
            "root_access_keys_present": bool(s.get("AccountAccessKeysPresent", 0)),
            "root_signing_certs_present": bool(
                s.get("AccountSigningCertificatesPresent", 0)
            ),
            "mfa_devices": s.get("MFADevices", 0),
            "users": s.get("Users", 0),
            "groups": s.get("Groups", 0),
            "roles": s.get("Roles", 0),
            "policies": s.get("Policies", 0),
        }
    ]


def iam_users(cfg):
    """
    One row per IAM user: MFA status, access-key count and oldest key age,
    whether a console password is set, and last password use.
    """
    iam = cfg["session"].client("iam")
    now = datetime.now(timezone.utc)
    rows = []
    for page in iam.get_paginator("list_users").paginate():
        rows.extend(_user_row(iam, u, now) for u in page["Users"])
    return rows


def _user_row(iam, user, now):
    name = user["UserName"]
    mfa = iam.list_mfa_devices(UserName=name).get("MFADevices", [])
    keys = iam.list_access_keys(UserName=name).get("AccessKeyMetadata", [])
    key_ages = [(now - k["CreateDate"]).days for k in keys]
    last_used = user.get("PasswordLastUsed")
    created = user.get("CreateDate")
    return {
        "user": name,
        "mfa_enabled": bool(mfa),
        "access_keys": len(keys),
        "oldest_key_age_days": max(key_ages) if key_ages else "",
        "console_password": _has_console_password(iam, name),
        "password_last_used": last_used.isoformat() if last_used else "",
        "created": created.isoformat() if created else "",
    }


def _has_console_password(iam, name):
    try:
        iam.get_login_profile(UserName=name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            return False
        raise


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
