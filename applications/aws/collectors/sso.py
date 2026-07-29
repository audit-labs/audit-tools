"""
Collect IAM Identity Center (SSO) permission-set assignments for an account.

Requires AWS Organizations + IAM Identity Center. Returns an empty list with a
warning if no Identity Center instance is available or the target account can't
be resolved. When no account name is configured, the current account is used.
"""

import sys

from botocore.exceptions import ClientError

from . import api


def sso_assignments(cfg):
    session = cfg["session"]
    sso = session.client("sso-admin")

    instances = sso.list_instances().get("Instances", [])
    if not instances:
        print(
            "Warning: no IAM Identity Center instance found -- skipping.",
            file=sys.stderr,
        )
        return []
    instance_arn = instances[0]["InstanceArn"]
    identity_store_id = instances[0]["IdentityStoreId"]

    account = _resolve_account(cfg)
    if not account:
        return []

    ids = session.client("identitystore")
    ps_cache = {}
    name_cache = {}
    rows = []

    for ps_arn in _provisioned_permission_sets(sso, instance_arn, account):
        assignments = _account_assignments(sso, instance_arn, account, ps_arn)
        if not assignments:
            continue
        ps = _permission_set(sso, instance_arn, ps_arn, ps_cache)
        for a in assignments:
            rows.append(
                {
                    "principal": _principal_name(ids, identity_store_id, a, name_cache),
                    "type": a["PrincipalType"],
                    "permission_set": ps["name"],
                    "managed_policies": ps["managed"],
                    "inline_policy": ps["inline"],
                }
            )
    return rows


def _resolve_account(cfg):
    """Resolve the target account ID from the configured account name, or fall
    back to the current account when no name is given."""
    name = cfg.get("account", "")
    if not name:
        return api.account_id(cfg)

    orgs = cfg["session"].client("organizations")
    try:
        for page in orgs.get_paginator("list_accounts").paginate():
            for acct in page["Accounts"]:
                if acct["Name"] == name and acct["Status"] == "ACTIVE":
                    return acct["Id"]
    except ClientError:
        print(
            "Warning: could not list organization accounts (needs the management "
            "account) -- skipping SSO assignments.",
            file=sys.stderr,
        )
        return ""

    print(f"Warning: no active account named '{name}' -- skipping.", file=sys.stderr)
    return ""


def _provisioned_permission_sets(sso, instance_arn, account):
    arns = []
    paginator = sso.get_paginator("list_permission_sets_provisioned_to_account")
    for page in paginator.paginate(InstanceArn=instance_arn, AccountId=account):
        arns.extend(page.get("PermissionSets", []))
    return arns


def _account_assignments(sso, instance_arn, account, ps_arn):
    out = []
    paginator = sso.get_paginator("list_account_assignments")
    for page in paginator.paginate(
        InstanceArn=instance_arn, AccountId=account, PermissionSetArn=ps_arn
    ):
        out.extend(page.get("AccountAssignments", []))
    return out


def _permission_set(sso, instance_arn, ps_arn, cache):
    if ps_arn in cache:
        return cache[ps_arn]
    name = sso.describe_permission_set(
        InstanceArn=instance_arn, PermissionSetArn=ps_arn
    )["PermissionSet"]["Name"]
    managed = [
        m["Arn"]
        for m in sso.list_managed_policies_in_permission_set(
            InstanceArn=instance_arn, PermissionSetArn=ps_arn
        ).get("AttachedManagedPolicies", [])
    ]
    inline = sso.get_inline_policy_for_permission_set(
        InstanceArn=instance_arn, PermissionSetArn=ps_arn
    ).get("InlinePolicy", "")
    cache[ps_arn] = {
        "name": name,
        "managed": ", ".join(managed) or "(none)",
        "inline": "yes" if inline else "no",
    }
    return cache[ps_arn]


def _principal_name(ids, store_id, assignment, cache):
    pid = assignment["PrincipalId"]
    if pid in cache:
        return cache[pid]
    ptype = assignment["PrincipalType"]
    name = pid
    try:
        if ptype == "USER":
            name = ids.describe_user(IdentityStoreId=store_id, UserId=pid).get(
                "UserName", pid
            )
        elif ptype == "GROUP":
            name = ids.describe_group(IdentityStoreId=store_id, GroupId=pid).get(
                "DisplayName", pid
            )
    except ClientError:
        pass
    cache[pid] = name
    return name
