"""Unit tests for the new GitHub security collectors, mocking the HTTP layer."""

import types

import pytest
import requests

from applications.github.collectors import (
    deploy_keys,
    org_settings,
    security_alerts,
    webhooks,
)

CFG = {"headers": {}, "timeout": 30}


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _http_error(status):
    err = requests.HTTPError()
    err.response = types.SimpleNamespace(status_code=status)
    return err


# --- org_security -----------------------------------------------------------


def test_org_security_row(monkeypatch):
    payload = {
        "two_factor_requirement_enabled": True,
        "default_repository_permission": "read",
        "members_can_create_repositories": False,
    }
    monkeypatch.setattr(org_settings.requests, "get", lambda *a, **k: _Resp(payload))
    rows = org_settings.org_security("acme", CFG)
    assert len(rows) == 1
    assert rows[0]["two_factor_required"] is True
    assert rows[0]["default_repo_permission"] == "read"
    assert rows[0]["members_can_create_repos"] is False


# --- webhooks ---------------------------------------------------------------


def test_webhooks_flags_insecure(monkeypatch):
    def fake_paginate(url, cfg, params=None):
        if url.endswith("/orgs/acme/hooks"):
            return [
                {
                    "config": {"url": "http://hook.example", "insecure_ssl": "1"},
                    "events": ["push"],
                    "active": True,
                }
            ]
        if url.endswith("/orgs/acme/repos"):
            return [{"name": "repo1"}]
        if url.endswith("/repos/acme/repo1/hooks"):
            return [
                {
                    "config": {"url": "https://secure.example", "insecure_ssl": "0"},
                    "events": ["pull_request"],
                    "active": True,
                }
            ]
        return []

    monkeypatch.setattr(webhooks, "paginate", fake_paginate)
    rows = webhooks.webhooks("acme", CFG)

    org_hook = next(r for r in rows if r["scope"] == "org")
    assert org_hook["insecure_url"] is True
    assert org_hook["ssl_verification"] == "disabled"

    repo_hook = next(r for r in rows if r["scope"] == "repo:repo1")
    assert repo_hook["insecure_url"] is False
    assert repo_hook["ssl_verification"] == "enabled"


def test_webhooks_skips_forbidden_repo(monkeypatch):
    def fake_paginate(url, cfg, params=None):
        if url.endswith("/orgs/acme/hooks"):
            return []
        if url.endswith("/orgs/acme/repos"):
            return [{"name": "locked"}]
        raise _http_error(403)

    monkeypatch.setattr(webhooks, "paginate", fake_paginate)
    assert webhooks.webhooks("acme", CFG) == []


# --- deploy_keys ------------------------------------------------------------


def test_deploy_keys_rows(monkeypatch):
    def fake_paginate(url, cfg, params=None):
        if url.endswith("/orgs/acme/repos"):
            return [{"name": "repo1"}]
        if url.endswith("/repos/acme/repo1/keys"):
            return [{"title": "ci", "read_only": False, "created_at": "2026-01-01"}]
        return []

    monkeypatch.setattr(deploy_keys, "paginate", fake_paginate)
    rows = deploy_keys.deploy_keys("acme", CFG)
    assert rows == [
        {
            "repo": "repo1",
            "title": "ci",
            "read_only": False,
            "created_at": "2026-01-01",
            "last_used": "",
            "added_by": "",
        }
    ]


# --- security alerts --------------------------------------------------------


def test_secret_scanning_rows(monkeypatch):
    monkeypatch.setattr(
        security_alerts,
        "paginate",
        lambda url, cfg, params=None: [
            {
                "repository": {"full_name": "acme/repo1"},
                "secret_type_display_name": "AWS Key",
                "state": "open",
            }
        ],
    )
    rows = security_alerts.secret_scanning("acme", CFG)
    assert rows[0]["repo"] == "acme/repo1"
    assert rows[0]["secret_type"] == "AWS Key"


def test_dependabot_rows(monkeypatch):
    monkeypatch.setattr(
        security_alerts,
        "paginate",
        lambda url, cfg, params=None: [
            {
                "repository": {"full_name": "acme/repo1"},
                "dependency": {"package": {"name": "requests"}},
                "security_advisory": {"severity": "high", "summary": "RCE"},
                "state": "open",
            }
        ],
    )
    rows = security_alerts.dependabot_alerts("acme", CFG)
    assert rows[0]["package"] == "requests"
    assert rows[0]["severity"] == "high"


@pytest.mark.parametrize(
    "fn", [security_alerts.secret_scanning, security_alerts.dependabot_alerts]
)
def test_alerts_skip_without_advanced_security(monkeypatch, fn):
    def raise_403(url, cfg, params=None):
        raise _http_error(403)

    monkeypatch.setattr(security_alerts, "paginate", raise_403)
    assert fn("acme", CFG) == []
