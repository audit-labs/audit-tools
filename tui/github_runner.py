"""
Drive the existing GitHub audit collectors from the TUI.

This module reuses the collectors and CSV reporter under
``applications/github`` unchanged. It exposes:

- ``CHECKS``: the list of available audit checks the UI presents.
- ``run_audit``: run the selected checks, write the same output package
  ``audit.py`` produces, and report progress through a callback.
"""

import os
import sys
from collections.abc import Iterable
from datetime import date

from tui.common import Check, ProgressCallback, ProgressEvent

# Import the GitHub collectors as a namespaced package so the GitHub and GitLab
# collector packages (both named ``collectors`` on disk) can coexist in one
# process. Requires the repo root on sys.path.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from applications.github.collectors import (
    audit_log,
    branch_protections,
    commits,
    members,
)
from applications.github.reporters import csv_reporter

# --- Check registry ---------------------------------------------------------

# For GitHub, ``arg`` is "base" -> fn(org, cfg), "collabs" -> fn(org, cfg,
# repo_collabs), or "branch" -> fn(org, cfg, branch).

CHECKS: list[Check] = [
    Check("member_roster", "Member roster", members.member_roster, "member_roster.csv"),
    Check(
        "two_factor",
        "2FA disabled",
        members.two_factor_disabled,
        "two_factor_disabled.csv",
        note="requires org owner token",
    ),
    Check(
        "outside_collaborators",
        "Outside collaborators",
        members.outside_collaborators,
        "outside_collaborators.csv",
        arg="collabs",
    ),
    Check(
        "privileged_access",
        "Privileged access",
        members.privileged_access,
        "privileged_access.csv",
        arg="collabs",
    ),
    Check(
        "pending_invitations",
        "Pending invitations",
        members.pending_invitations,
        "pending_invitations.csv",
    ),
    Check(
        "team_permissions",
        "Team permissions",
        members.team_permissions,
        "team_permissions.csv",
    ),
    Check(
        "permission_matrix",
        "Permission matrix",
        members.permission_matrix,
        "permission_matrix.csv",
        arg="collabs",
    ),
    Check(
        "branch_protections",
        "Branch protections",
        branch_protections.branch_protections,
        "branch_protections.csv",
    ),
    Check("commits", "Commits", commits.commits, "commits.csv", arg="branch"),
    Check(
        "audit_log",
        "Audit log (branch/ruleset changes)",
        audit_log.audit_log,
        "audit_log.csv",
        note="requires GitHub Enterprise Cloud",
    ),
]

DEFAULT_SELECTION = [c.key for c in CHECKS if c.key != "audit_log"]


# --- Config + output helpers ------------------------------------------------


def build_cfg(token: str) -> dict:
    """Build the config dict the collectors expect (mirrors config.load())."""
    return {
        "token": token,
        "headers": {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        "timeout": 30,
    }


def default_output_dir(out: str, org: str) -> str:
    """Match the folder naming used by audit.py."""
    return os.path.join(out, f"github_audit_{org}_{date.today().isoformat()}")


# --- Runner -----------------------------------------------------------------


def run_audit(
    *,
    org: str,
    token: str,
    output_dir: str,
    branch: str,
    selected_keys: Iterable[str],
    on_event: ProgressCallback,
) -> list[tuple[str, int]]:
    """
    Run the selected checks and write the audit package to ``output_dir``.

    A collector that raises is reported as an error and recorded with a count
    of 0, matching audit.py's behavior of never aborting the whole run.

    Returns the list of (label, row_count) sections that was written to the
    summary file.
    """
    cfg = build_cfg(token)
    selected = set(selected_keys)
    checks = [c for c in CHECKS if c.key in selected]

    repo_collabs: list | None = None
    if any(c.arg == "collabs" for c in checks):
        on_event(ProgressEvent("fetch", "Repo collaborators (shared cache)"))
        try:
            repo_collabs = members.fetch_repo_collaborators(org, cfg)
        except Exception as e:  # noqa: BLE001 - surface, keep going
            on_event(
                ProgressEvent(
                    "error", "Repo collaborators (shared cache)", message=str(e)
                )
            )
            repo_collabs = []

    sections: list[tuple[str, int]] = []
    for c in checks:
        on_event(ProgressEvent("start", c.label))
        try:
            if c.arg == "collabs":
                rows = c.fn(org, cfg, repo_collabs or [])
            elif c.arg == "branch":
                rows = c.fn(org, cfg, branch)
            else:
                rows = c.fn(org, cfg)
        except Exception as e:  # noqa: BLE001 - one bad check shouldn't kill the run
            on_event(ProgressEvent("error", c.label, message=str(e)))
            sections.append((c.label, 0))
            continue

        csv_reporter.write(output_dir, c.filename, rows)
        sections.append((c.label, len(rows)))
        on_event(ProgressEvent("done", c.label, count=len(rows)))

    csv_reporter.write_summary(output_dir, org, sections)
    total = sum(n for _, n in sections)
    on_event(ProgressEvent("summary", output_dir, count=total))
    return sections
