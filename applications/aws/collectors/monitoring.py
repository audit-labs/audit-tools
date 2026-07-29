"""
Collect audit-logging posture: CloudTrail trails and AWS Config recorders.
"""

import sys

from botocore.exceptions import ClientError

from .api import enabled_regions


def cloudtrail(cfg):
    """
    One row per CloudTrail trail: whether it is logging, multi-region, and has
    log-file validation. An empty result means no trails are configured.
    """
    region = cfg.get("region") or "us-east-1"
    ct = cfg["session"].client("cloudtrail", region_name=region)
    rows = []
    for trail in ct.describe_trails(includeShadowTrails=False).get("trailList", []):
        try:
            status = ct.get_trail_status(Name=trail["TrailARN"])
        except ClientError:
            status = {}
        rows.append(
            {
                "name": trail.get("Name", ""),
                "home_region": trail.get("HomeRegion", ""),
                "multi_region": trail.get("IsMultiRegionTrail"),
                "log_file_validation": trail.get("LogFileValidationEnabled"),
                "is_logging": status.get("IsLogging"),
                "s3_bucket": trail.get("S3BucketName", ""),
            }
        )
    return rows


def config_recorders(cfg):
    """
    One row per region: whether AWS Config is recording. Regions with no
    recorder are reported so gaps are visible.
    """
    session = cfg["session"]
    rows = []
    for region in enabled_regions(cfg):
        try:
            cc = session.client("config", region_name=region)
            recorders = cc.describe_configuration_recorders().get(
                "ConfigurationRecorders", []
            )
            statuses = {
                s["name"]: s
                for s in cc.describe_configuration_recorder_status().get(
                    "ConfigurationRecordersStatus", []
                )
            }
        except ClientError as e:
            print(f"  Skipping {region}: config returned {e}", file=sys.stderr)
            continue

        if not recorders:
            rows.append(
                {
                    "region": region,
                    "recorder": "(none)",
                    "recording": False,
                    "last_status": "",
                }
            )
            continue
        for r in recorders:
            st = statuses.get(r["name"], {})
            rows.append(
                {
                    "region": region,
                    "recorder": r["name"],
                    "recording": st.get("recording"),
                    "last_status": st.get("lastStatus", ""),
                }
            )
    return rows
