"""Unit tests for the new AWS security collectors, mocking boto3 clients."""

from unittest.mock import MagicMock

from applications.aws.collectors import iam as aws_iam
from applications.aws.collectors import monitoring
from applications.aws.collectors import security_groups as sg


class FakeSession:
    """Dispatch .client(service, region_name=...) to preconfigured mocks."""

    def __init__(self, clients):
        self._clients = clients

    def client(self, service, region_name=None):
        return self._clients[service]


def _cfg(clients):
    return {"session": FakeSession(clients), "region": "us-east-1"}


# --- account_security -------------------------------------------------------


def test_account_security():
    iam = MagicMock()
    iam.get_account_summary.return_value = {
        "SummaryMap": {
            "AccountMFAEnabled": 1,
            "AccountAccessKeysPresent": 0,
            "Users": 5,
            "Roles": 12,
        }
    }
    rows = aws_iam.account_security(_cfg({"iam": iam}))
    assert rows[0]["root_mfa_enabled"] is True
    assert rows[0]["root_access_keys_present"] is False
    assert rows[0]["users"] == 5
    assert rows[0]["roles"] == 12


# --- cloudtrail -------------------------------------------------------------


def test_cloudtrail():
    ct = MagicMock()
    ct.describe_trails.return_value = {
        "trailList": [
            {
                "Name": "org-trail",
                "TrailARN": "arn:aws:cloudtrail:...:trail/org-trail",
                "HomeRegion": "us-east-1",
                "IsMultiRegionTrail": True,
                "LogFileValidationEnabled": True,
                "S3BucketName": "logs",
            }
        ]
    }
    ct.get_trail_status.return_value = {"IsLogging": True}
    rows = monitoring.cloudtrail(_cfg({"cloudtrail": ct}))
    assert rows[0]["is_logging"] is True
    assert rows[0]["multi_region"] is True
    assert rows[0]["s3_bucket"] == "logs"


# --- config_recorders -------------------------------------------------------


def _ec2_one_region():
    ec2 = MagicMock()
    ec2.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}
    return ec2


def test_config_recorders_recording():
    config = MagicMock()
    config.describe_configuration_recorders.return_value = {
        "ConfigurationRecorders": [{"name": "default"}]
    }
    config.describe_configuration_recorder_status.return_value = {
        "ConfigurationRecordersStatus": [
            {"name": "default", "recording": True, "lastStatus": "SUCCESS"}
        ]
    }
    rows = monitoring.config_recorders(
        _cfg({"ec2": _ec2_one_region(), "config": config})
    )
    assert rows == [
        {
            "region": "us-east-1",
            "recorder": "default",
            "recording": True,
            "last_status": "SUCCESS",
        }
    ]


def test_config_recorders_reports_gap():
    config = MagicMock()
    config.describe_configuration_recorders.return_value = {
        "ConfigurationRecorders": []
    }
    config.describe_configuration_recorder_status.return_value = {
        "ConfigurationRecordersStatus": []
    }
    rows = monitoring.config_recorders(
        _cfg({"ec2": _ec2_one_region(), "config": config})
    )
    assert rows[0]["recorder"] == "(none)"
    assert rows[0]["recording"] is False


# --- security_groups --------------------------------------------------------


def _ec2_with_groups(groups):
    ec2 = _ec2_one_region()
    paginator = MagicMock()
    paginator.paginate.return_value = [{"SecurityGroups": groups}]
    ec2.get_paginator.return_value = paginator
    return ec2


def test_security_groups_flags_open_ingress():
    groups = [
        {
            "GroupId": "sg-1",
            "GroupName": "web",
            "IpPermissions": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                    "Ipv6Ranges": [],
                }
            ],
        }
    ]
    rows = sg.security_groups(_cfg({"ec2": _ec2_with_groups(groups)}))
    assert len(rows) == 1
    assert rows[0]["group_id"] == "sg-1"
    assert rows[0]["from_port"] == 22
    assert rows[0]["open_to"] == "0.0.0.0/0"


def test_security_groups_ignores_scoped_ingress():
    groups = [
        {
            "GroupId": "sg-2",
            "GroupName": "internal",
            "IpPermissions": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 5432,
                    "ToPort": 5432,
                    "IpRanges": [{"CidrIp": "10.0.0.0/8"}],
                    "Ipv6Ranges": [],
                }
            ],
        }
    ]
    rows = sg.security_groups(_cfg({"ec2": _ec2_with_groups(groups)}))
    assert rows == []
