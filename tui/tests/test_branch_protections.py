"""Tests for branch-protection collection, covering classic + ruleset merge."""

import types

from applications.github.collectors import branch_protections as bp

CFG = {"headers": {}, "timeout": 30}


def _classic_get(status, payload=None):
    """Fake requests.get for the classic protection endpoint."""

    def _get(*args, **kwargs):
        return types.SimpleNamespace(
            status_code=status,
            raise_for_status=lambda: None,
            json=lambda: payload or {},
        )

    return _get


def _paginate(rules):
    """Fake api.paginate returning one repo, one 'main' branch, and `rules`."""

    def _p(url, cfg, params=None):
        if url.endswith("/orgs/acme/repos"):
            return [{"name": "repo1"}]
        if url.endswith("/repos/acme/repo1/branches"):
            return [{"name": "main"}]
        if "/rules/branches/main" in url:
            return rules
        return []

    return _p


def _run(monkeypatch, rules, classic_status, classic_payload=None):
    monkeypatch.setattr(bp, "paginate", _paginate(rules))
    monkeypatch.setattr(
        bp.requests, "get", _classic_get(classic_status, classic_payload)
    )
    rows = bp.branch_protections("acme", CFG)
    assert len(rows) == 1
    return rows[0]


def test_ruleset_only_is_reported_protected(monkeypatch):
    rules = [
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": 2,
                "require_code_owner_review": True,
                "dismiss_stale_reviews_on_push": True,
            },
        },
        {"type": "non_fast_forward", "parameters": {}},
    ]
    row = _run(monkeypatch, rules, classic_status=404)
    assert row["protected"] is True
    assert row["protection_source"] == "ruleset"
    assert row["required_reviews"] == 2
    assert row["require_code_owner_reviews"] is True
    assert row["dismiss_stale_reviews"] is True


def test_ruleset_status_checks(monkeypatch):
    rules = [
        {
            "type": "required_status_checks",
            "parameters": {
                "required_status_checks": [
                    {"context": "build"},
                    {"context": "lint"},
                ]
            },
        }
    ]
    row = _run(monkeypatch, rules, classic_status=404)
    assert row["required_status_checks"] == "build, lint"


def test_classic_only(monkeypatch):
    payload = {
        "required_pull_request_reviews": {"required_approving_review_count": 1},
        "enforce_admins": {"enabled": True},
    }
    row = _run(monkeypatch, rules=[], classic_status=200, classic_payload=payload)
    assert row["protected"] is True
    assert row["protection_source"] == "branch protection"
    assert row["required_reviews"] == 1
    assert row["enforce_admins"] is True


def test_both_sources(monkeypatch):
    payload = {"required_pull_request_reviews": {"required_approving_review_count": 3}}
    rules = [{"type": "pull_request", "parameters": {}}]
    row = _run(monkeypatch, rules, classic_status=200, classic_payload=payload)
    assert row["protection_source"] == "branch protection + ruleset"
    # Classic values win when both are present.
    assert row["required_reviews"] == 3


def test_no_protection(monkeypatch):
    row = _run(monkeypatch, rules=[], classic_status=404)
    assert row["protected"] is False
    assert row["protection_source"] == ""
    assert row["required_reviews"] is None
