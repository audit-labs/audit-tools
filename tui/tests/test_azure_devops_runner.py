"""Tests for the TUI's Azure DevOps audit orchestration.

Stub the network-bound collectors and verify run_audit's wiring: base vs
project-scoped dispatch, the shared project cache, per-check error handling,
and that the CSV package (per-check files + summary) is written.
"""

import csv
import os

import pytest

from tui import azure_devops_runner as r


@pytest.fixture
def fake_checks(monkeypatch):
    calls = {}

    def base_fn(cfg):
        calls["base"] = cfg
        return [{"user": "alice"}, {"user": "bob"}]

    def projects_fn(cfg, projects):
        calls["projects"] = (cfg, projects)
        return [{"project": p["name"]} for p in projects]

    def boom_fn(cfg):
        raise RuntimeError("kaboom")

    checks = [
        r.Check("base", "Base", base_fn, "base.csv"),
        r.Check("projects", "Projects", projects_fn, "projects.csv", arg="projects"),
        r.Check("boom", "Boom", boom_fn, "boom.csv"),
    ]
    monkeypatch.setattr(r, "CHECKS", checks)

    # Avoid building a real auth header / hitting the network.
    monkeypatch.setattr(
        r.api,
        "build_cfg",
        lambda org, pat, base_url: {"org": org, "base_url": base_url},
    )

    fetch_calls = []

    def fake_fetch(cfg):
        fetch_calls.append(cfg["org"])
        return [{"id": "p1", "name": "Proj One"}]

    monkeypatch.setattr(r.core, "fetch_projects", fake_fetch)

    return calls, fetch_calls


def run(tmp_path, keys, base_url="https://dev.azure.com"):
    events = []
    sections = r.run_audit(
        org="acme",
        pat="pat",
        base_url=base_url,
        output_dir=str(tmp_path),
        selected_keys=keys,
        on_event=events.append,
    )
    return events, sections


def test_dispatch_and_files(tmp_path, fake_checks):
    calls, _ = fake_checks
    run(tmp_path, ["base", "projects"])

    assert calls["base"]["org"] == "acme"
    assert calls["projects"][1] == [{"id": "p1", "name": "Proj One"}]

    for name in ("base.csv", "projects.csv", "summary.txt"):
        assert os.path.exists(tmp_path / name), name

    with open(tmp_path / "projects.csv", newline="") as f:
        assert list(csv.DictReader(f)) == [{"project": "Proj One"}]


def test_project_cache_fetched_once(tmp_path, fake_checks):
    _, fetch_calls = fake_checks
    run(tmp_path, ["projects", "base"])
    assert fetch_calls == ["acme"]


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


def test_all_checks_on_by_default():
    assert r.DEFAULT_SELECTION == [c.key for c in r.CHECKS]
    assert "branch_policies" in r.DEFAULT_SELECTION
    assert "service_connections" in r.DEFAULT_SELECTION
