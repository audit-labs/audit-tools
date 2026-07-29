"""Tests for the TUI's GitLab audit orchestration.

Stub the network-bound collectors and verify run_audit's wiring: base vs
project-scoped dispatch, the shared project cache, per-check error handling,
and that the CSV package (per-check files + summary) is written.
"""

import csv
import os

import pytest

from tui import gitlab_runner as r


@pytest.fixture
def fake_checks(monkeypatch):
    calls = {}

    def base_fn(group, cfg):
        calls["base"] = (group, cfg)
        return [{"username": "alice"}, {"username": "bob"}]

    def projects_fn(group, cfg, projects):
        calls["projects"] = (group, cfg, projects)
        return [{"project": p["path_with_namespace"]} for p in projects]

    def boom_fn(group, cfg):
        raise RuntimeError("kaboom")

    checks = [
        r.Check("base", "Base", base_fn, "base.csv"),
        r.Check("projects", "Projects", projects_fn, "projects.csv", arg="projects"),
        r.Check("boom", "Boom", boom_fn, "boom.csv"),
    ]
    monkeypatch.setattr(r, "CHECKS", checks)

    fetch_calls = []

    def fake_fetch(group, cfg):
        fetch_calls.append(group)
        return [{"id": 1, "path_with_namespace": "grp/proj"}]

    monkeypatch.setattr(r.projects, "fetch_projects", fake_fetch)

    return calls, fetch_calls


def run(tmp_path, keys, base_url="https://gitlab.com/api/v4"):
    events = []
    sections = r.run_audit(
        group="grp",
        token="tok",
        base_url=base_url,
        output_dir=str(tmp_path),
        selected_keys=keys,
        on_event=events.append,
    )
    return events, sections


def test_argument_dispatch_and_files(tmp_path, fake_checks):
    calls, _ = fake_checks
    run(tmp_path, ["base", "projects"])

    assert calls["base"][0] == "grp"
    assert calls["projects"][2] == [{"id": 1, "path_with_namespace": "grp/proj"}]

    for name in ("base.csv", "projects.csv", "summary.txt"):
        assert os.path.exists(tmp_path / name), name

    with open(tmp_path / "projects.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows == [{"project": "grp/proj"}]


def test_project_cache_fetched_once(tmp_path, fake_checks):
    _, fetch_calls = fake_checks
    run(tmp_path, ["projects", "base"])
    assert fetch_calls == ["grp"]


def test_project_cache_skipped_when_not_needed(tmp_path, fake_checks):
    _, fetch_calls = fake_checks
    run(tmp_path, ["base"])
    assert fetch_calls == []


def test_failing_check_does_not_abort_run(tmp_path, fake_checks):
    events, sections = run(tmp_path, ["boom", "base"])

    kinds = [(e.kind, e.label) for e in events]
    assert ("error", "Boom") in kinds
    assert ("done", "Base") in kinds

    labels = dict(sections)
    assert labels["Boom"] == 0
    assert labels["Base"] == 2


def test_base_url_reaches_cfg(tmp_path, fake_checks):
    calls, _ = fake_checks
    run(tmp_path, ["base"], base_url="https://gitlab.example.com/api/v4/")
    # build_cfg strips the trailing slash.
    assert calls["base"][1]["base_url"] == "https://gitlab.example.com/api/v4"
    assert calls["base"][1]["headers"]["PRIVATE-TOKEN"] == "tok"


def test_premium_checks_off_by_default():
    assert "approval_rules" not in r.DEFAULT_SELECTION
    assert "audit_events" not in r.DEFAULT_SELECTION
    assert "password_policy" not in r.DEFAULT_SELECTION
    assert "group_members" in r.DEFAULT_SELECTION
