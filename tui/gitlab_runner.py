"""
Drive the GitLab audit collectors from the TUI.

Reuses the collectors and CSV reporter under ``applications/gitlab`` unchanged.
Mirrors github_runner: a ``CHECKS`` registry plus ``run_audit`` that writes the
same package ``applications/gitlab/audit.py`` produces and reports progress
through a callback.
"""

import os
import sys
from collections.abc import Iterable
from datetime import date

from tui.common import Check, ProgressCallback, ProgressEvent

# Namespaced import so the GitHub and GitLab collector packages (both named
# ``collectors`` on disk) can coexist in one process.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from applications.gitlab.collectors import (
    approvals,
    audit_events,
    branch_protections,
    members,
    pipelines,
    projects,
    settings,
)
from applications.gitlab.reporters import csv_reporter

# --- Check registry ---------------------------------------------------------

# For GitLab, ``arg`` is "base" -> fn(group, cfg) or "projects" -> fn(group,
# cfg, projects), where the project cache is fetched once and shared.

CHECKS: list[Check] = [
    Check("group_members", "Group members", members.group_members, "group_members.csv"),
    Check(
        "projects", "Projects", projects.project_list, "projects.csv", arg="projects"
    ),
    Check(
        "project_members",
        "Project members",
        members.project_members,
        "project_members.csv",
        arg="projects",
    ),
    Check(
        "branch_protections",
        "Branch protections",
        branch_protections.branch_protections,
        "branch_protections.csv",
        arg="projects",
    ),
    Check(
        "pipelines",
        "Pipelines",
        pipelines.pipelines,
        "pipelines.csv",
        arg="projects",
    ),
    Check(
        "approval_rules",
        "Approval rules",
        approvals.approval_rules,
        "approval_rules.csv",
        arg="projects",
        note="requires Premium/Ultimate",
    ),
    Check(
        "audit_events",
        "Audit events",
        audit_events.audit_events,
        "audit_events.csv",
        note="requires Premium/Ultimate",
    ),
    Check(
        "password_policy",
        "Password policy",
        settings.password_policy,
        "password_policy.csv",
        note="self-hosted, admin token",
    ),
]

_PREMIUM = {"approval_rules", "audit_events", "password_policy"}
DEFAULT_SELECTION = [c.key for c in CHECKS if c.key not in _PREMIUM]


# --- Config + output helpers ------------------------------------------------


def build_cfg(token: str, base_url: str) -> dict:
    """Build the config dict the collectors expect (mirrors config.load())."""
    return {
        "token": token,
        "base_url": base_url.rstrip("/"),
        "headers": {"PRIVATE-TOKEN": token},
        "timeout": 30,
    }


def default_output_dir(out: str, group: str) -> str:
    """Match the folder naming used by applications/gitlab/audit.py."""
    safe_group = group.replace("/", "-")
    return os.path.join(out, f"gitlab_audit_{safe_group}_{date.today().isoformat()}")


# --- Runner -----------------------------------------------------------------


def run_audit(
    *,
    group: str,
    token: str,
    base_url: str,
    output_dir: str,
    selected_keys: Iterable[str],
    on_event: ProgressCallback,
) -> list[tuple[str, int]]:
    """
    Run the selected checks and write the audit package to ``output_dir``.

    A collector that raises is reported as an error and recorded with a count
    of 0, so one bad check never aborts the whole run.
    """
    cfg = build_cfg(token, base_url)
    selected = set(selected_keys)
    checks = [c for c in CHECKS if c.key in selected]

    project_cache: list | None = None
    if any(c.arg == "projects" for c in checks):
        on_event(ProgressEvent("fetch", "Projects (shared cache)"))
        try:
            project_cache = projects.fetch_projects(group, cfg)
        except Exception as e:
            on_event(ProgressEvent("error", "Projects (shared cache)", message=str(e)))
            project_cache = []

    sections: list[tuple[str, int]] = []
    for c in checks:
        on_event(ProgressEvent("start", c.label))
        try:
            if c.arg == "projects":
                rows = c.fn(group, cfg, project_cache or [])
            else:
                rows = c.fn(group, cfg)
        except Exception as e:
            on_event(ProgressEvent("error", c.label, message=str(e)))
            sections.append((c.label, 0))
            continue

        csv_reporter.write(output_dir, c.filename, rows)
        sections.append((c.label, len(rows)))
        on_event(ProgressEvent("done", c.label, count=len(rows)))

    csv_reporter.write_summary(output_dir, group, sections)
    total = sum(n for _, n in sections)
    on_event(ProgressEvent("summary", output_dir, count=total))
    return sections
