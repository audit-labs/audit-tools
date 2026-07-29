"""
Collect security-group ingress rules open to the internet, across all regions.

Only rules allowing 0.0.0.0/0 or ::/0 are reported — one row per open rule.
"""

import sys

from botocore.exceptions import ClientError

from .api import enabled_regions

OPEN_V4 = "0.0.0.0/0"
OPEN_V6 = "::/0"


def security_groups(cfg):
    session = cfg["session"]
    rows = []
    for region in enabled_regions(cfg):
        try:
            ec2 = session.client("ec2", region_name=region)
            groups = _all_groups(ec2)
        except ClientError as e:
            print(f"  Skipping {region}: ec2 returned {e}", file=sys.stderr)
            continue
        for sg in groups:
            rows.extend(_open_rules(region, sg))
    return rows


def _all_groups(ec2):
    groups = []
    for page in ec2.get_paginator("describe_security_groups").paginate():
        groups.extend(page.get("SecurityGroups", []))
    return groups


def _open_rules(region, sg):
    rows = []
    for perm in sg.get("IpPermissions", []):
        open_to = [
            r["CidrIp"] for r in perm.get("IpRanges", []) if r.get("CidrIp") == OPEN_V4
        ]
        open_to += [
            r["CidrIpv6"]
            for r in perm.get("Ipv6Ranges", [])
            if r.get("CidrIpv6") == OPEN_V6
        ]
        if not open_to:
            continue
        rows.append(
            {
                "region": region,
                "group_id": sg.get("GroupId", ""),
                "group_name": sg.get("GroupName", ""),
                "protocol": perm.get("IpProtocol", ""),
                "from_port": perm.get("FromPort", "all"),
                "to_port": perm.get("ToPort", "all"),
                "open_to": ", ".join(open_to),
            }
        )
    return rows
