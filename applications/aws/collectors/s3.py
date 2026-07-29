"""
Collect S3 bucket public-access exposure.

For each bucket, reports the Public Access Block state, whether S3 considers the
bucket policy public, and whether the ACL grants access to AllUsers.
"""

from botocore.exceptions import ClientError

ALL_USERS = "http://acs.amazonaws.com/groups/global/AllUsers"


def s3_public_access(cfg):
    s3 = cfg["session"].client("s3")
    rows = []
    for b in s3.list_buckets().get("Buckets", []):
        name = b["Name"]
        rows.append(
            {
                "bucket": name,
                "region": _bucket_region(s3, name),
                "public_access_block": _pab_status(s3, name),
                "policy_public": _policy_public(s3, name),
                "acl_public": _acl_public(s3, name),
            }
        )
    return rows


def _bucket_region(s3, name):
    try:
        loc = s3.get_bucket_location(Bucket=name).get("LocationConstraint")
        return loc or "us-east-1"
    except ClientError:
        return "unknown"


def _pab_status(s3, name):
    try:
        pab = s3.get_public_access_block(Bucket=name)["PublicAccessBlockConfiguration"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchPublicAccessBlockConfiguration":
            return "MISSING"
        return "error"
    all_on = all(
        [
            pab.get("BlockPublicAcls"),
            pab.get("IgnorePublicAcls"),
            pab.get("BlockPublicPolicy"),
            pab.get("RestrictPublicBuckets"),
        ]
    )
    return "fully-restricted" if all_on else "partial"


def _policy_public(s3, name):
    try:
        return s3.get_bucket_policy_status(Bucket=name)["PolicyStatus"]["IsPublic"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
            return False
        return "error"


def _acl_public(s3, name):
    try:
        grants = s3.get_bucket_acl(Bucket=name).get("Grants", [])
    except ClientError:
        return "error"
    return any(g.get("Grantee", {}).get("URI") == ALL_USERS for g in grants)
