"""Tests for the TUI's AWS audit orchestration.

Stub the boto3 session and the collectors, then verify run_audit's wiring:
each check is called with the config, per-check errors don't abort the run, a
failed session build is reported cleanly, and the CSV package is written.
"""

import csv
import os

import pytest

from tui import aws_runner as r


@pytest.fixture
def fake_checks(monkeypatch):
    calls = {}

    def users_fn(cfg):
        calls["users"] = cfg
        return [{"user": "alice"}, {"user": "bob"}]

    def policy_fn(cfg):
        calls["policy"] = cfg
        return [{"minimum_length": 14}]

    def boom_fn(cfg):
        raise RuntimeError("kaboom")

    checks = [
        r.Check("users", "Users", users_fn, "users.csv"),
        r.Check("policy", "Policy", policy_fn, "policy.csv"),
        r.Check("boom", "Boom", boom_fn, "boom.csv"),
    ]
    monkeypatch.setattr(r, "CHECKS", checks)

    # Replace build_cfg so no real boto3 session is created.
    monkeypatch.setattr(
        r.api,
        "build_cfg",
        lambda profile, region, account: {
            "session": "SESSION",
            "profile": profile,
            "region": region,
            "account": account,
        },
    )
    return calls


def run(tmp_path, keys, profile="", region="us-east-1", account=""):
    events = []
    sections = r.run_audit(
        profile=profile,
        region=region,
        account=account,
        output_dir=str(tmp_path),
        selected_keys=keys,
        on_event=events.append,
    )
    return events, sections


def test_dispatch_and_files(tmp_path, fake_checks):
    calls = fake_checks
    run(tmp_path, ["users", "policy"], region="eu-west-1")

    # Each collector received the config dict.
    assert calls["users"]["region"] == "eu-west-1"
    assert calls["policy"]["session"] == "SESSION"

    for name in ("users.csv", "policy.csv", "summary.txt"):
        assert os.path.exists(tmp_path / name), name

    with open(tmp_path / "users.csv", newline="") as f:
        assert len(list(csv.DictReader(f))) == 2


def test_failing_check_does_not_abort_run(tmp_path, fake_checks):
    events, sections = run(tmp_path, ["boom", "users"])

    kinds = [(e.kind, e.label) for e in events]
    assert ("error", "Boom") in kinds
    assert ("done", "Users") in kinds

    labels = dict(sections)
    assert labels["Boom"] == 0
    assert labels["Users"] == 2


def test_session_build_failure_is_reported(tmp_path, fake_checks, monkeypatch):
    def boom_cfg(profile, region, account):
        raise RuntimeError("ProfileNotFound")

    monkeypatch.setattr(r.api, "build_cfg", boom_cfg)

    events, sections = run(tmp_path, ["users"], profile="ghost")

    kinds = [(e.kind, e.label) for e in events]
    assert ("error", "AWS session") in kinds
    # Run still ends with a summary and writes the (empty) package.
    summary = [e for e in events if e.kind == "summary"]
    assert summary
    assert summary[0].count == 0
    assert sections == []
    assert os.path.exists(tmp_path / "summary.txt")


def test_subject_defaults_to_default(tmp_path, fake_checks):
    run(tmp_path, ["users"], profile="")
    # An empty profile is folder-named "default".
    assert r.default_output_dir("./out", "") == r.default_output_dir("./out", "default")


def test_sso_off_by_default():
    assert "sso_assignments" not in r.DEFAULT_SELECTION
    assert "iam_users" in r.DEFAULT_SELECTION
