"""Tests for the TUI's GitHub audit orchestration.

These stub out the network-bound collectors and verify run_audit's wiring:
argument dispatch, the shared collaborator cache, per-check error handling,
and that the CSV package (per-check files + summary) is written.
"""

import csv
import os

import pytest

from tui import github_runner as r


@pytest.fixture
def fake_checks(monkeypatch):
    """Replace the real registry with stubbed collectors and record calls."""
    calls = {}

    def base_fn(org, cfg):
        calls["base"] = (org, cfg)
        return [{"login": "alice"}, {"login": "bob"}]

    def collabs_fn(org, cfg, repo_collabs):
        calls["collabs"] = (org, cfg, repo_collabs)
        return [{"repo": e["repo"]} for e in repo_collabs]

    def branch_fn(org, cfg, branch):
        calls["branch"] = (org, cfg, branch)
        return [{"branch": branch}]

    def boom_fn(org, cfg):
        raise RuntimeError("kaboom")

    checks = [
        r.Check("base", "Base", base_fn, "base.csv"),
        r.Check("collabs", "Collabs", collabs_fn, "collabs.csv", arg="collabs"),
        r.Check("branch", "Branch", branch_fn, "branch.csv", arg="branch"),
        r.Check("boom", "Boom", boom_fn, "boom.csv"),
    ]
    monkeypatch.setattr(r, "CHECKS", checks)

    fetch_calls = []

    def fake_fetch(org, cfg):
        fetch_calls.append(org)
        return [{"repo": "repo1", "collaborators": []}]

    monkeypatch.setattr(r.members, "fetch_repo_collaborators", fake_fetch)

    return calls, fetch_calls


def run(tmp_path, keys, fake_checks, branch="main"):
    events = []
    sections = r.run_audit(
        org="acme",
        token="tok",
        output_dir=str(tmp_path),
        branch=branch,
        selected_keys=keys,
        on_event=events.append,
    )
    return events, sections


def test_argument_dispatch_and_files(tmp_path, fake_checks):
    calls, _ = fake_checks
    run(tmp_path, ["base", "collabs", "branch"], fake_checks, "dev")

    # Each collector was called with the right signature.
    assert calls["base"][0] == "acme"
    assert calls["collabs"][2] == [{"repo": "repo1", "collaborators": []}]
    assert calls["branch"][2] == "dev"

    # CSV files were written for each check, plus the summary.
    for name in ("base.csv", "collabs.csv", "branch.csv", "summary.txt"):
        assert os.path.exists(tmp_path / name), name

    with open(tmp_path / "base.csv", newline="") as f:
        assert len(list(csv.DictReader(f))) == 2


def test_collab_cache_fetched_once(tmp_path, fake_checks):
    _, fetch_calls = fake_checks
    run(tmp_path, ["collabs", "base"], fake_checks)
    assert fetch_calls == ["acme"]  # fetched exactly once


def test_collab_cache_skipped_when_not_needed(tmp_path, fake_checks):
    _, fetch_calls = fake_checks
    run(tmp_path, ["base"], fake_checks)
    assert fetch_calls == []  # no collabs check selected -> no fetch


def test_failing_check_does_not_abort_run(tmp_path, fake_checks):
    events, sections = run(tmp_path, ["boom", "base"], fake_checks)

    kinds = [(e.kind, e.label) for e in events]
    assert ("error", "Boom") in kinds
    assert ("done", "Base") in kinds  # base still ran after boom failed

    labels = dict(sections)
    assert labels["Boom"] == 0
    assert labels["Base"] == 2


def test_summary_event_totals_rows(tmp_path, fake_checks):
    events, _ = run(tmp_path, ["base", "branch"], fake_checks)
    summary = [e for e in events if e.kind == "summary"]
    assert len(summary) == 1
    assert summary[0].count == 3  # 2 base + 1 branch
    assert summary[0].label == str(tmp_path)
