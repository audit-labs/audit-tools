"""
Drive the Azure DevOps audit collectors from the TUI.

Reuses the collectors and CSV reporter under ``applications/azure_devops``
unchanged. Mirrors the other runners: a ``CHECKS`` registry plus ``run_audit``
that writes the same package ``applications/azure_devops/audit.py`` produces and
reports progress through a callback.

``arg`` is "base" -> fn(cfg) (org-level) or "projects" -> fn(cfg, projects),
where the project cache is fetched once and shared.
"""

import os
import sys
from collections.abc import Iterable
from datetime import date

from tui.common import Check, ProgressCallback, ProgressEvent

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from applications.azure_devops.collectors import api, core, identity, pipelines, repos
from applications.azure_devops.reporters import csv_reporter

# --- Check registry ---------------------------------------------------------

CHECKS: list[Check] = [
    Check("projects", "Projects", core.project_list, "projects.csv", arg="projects"),
    Check(
        "user_entitlements",
        "User entitlements",
        identity.user_entitlements,
        "user_entitlements.csv",
    ),
    Check(
        "group_memberships",
        "Group memberships",
        identity.group_memberships,
        "group_memberships.csv",
        note="needs graph read scope",
    ),
    Check(
        "repositories",
        "Repositories",
        repos.repositories,
        "repositories.csv",
        arg="projects",
    ),
    Check(
        "branch_policies",
        "Branch policies",
        repos.branch_policies,
        "branch_policies.csv",
        arg="projects",
    ),
    Check(
        "service_connections",
        "Service connections",
        pipelines.service_connections,
        "service_connections.csv",
        arg="projects",
    ),
]

DEFAULT_SELECTION = [c.key for c in CHECKS]


# --- Config + output helpers ------------------------------------------------


def default_output_dir(out: str, org: str) -> str:
    """Match the folder naming used by applications/azure_devops/audit.py."""
    safe_org = org.replace("/", "-")
    return os.path.join(
        out, f"azure_devops_audit_{safe_org}_{date.today().isoformat()}"
    )


# --- Runner -----------------------------------------------------------------


def run_audit(
    *,
    org: str,
    pat: str,
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
    cfg = api.build_cfg(org, pat, base_url)
    selected = set(selected_keys)
    checks = [c for c in CHECKS if c.key in selected]

    project_cache: list | None = None
    if any(c.arg == "projects" for c in checks):
        on_event(ProgressEvent("fetch", "Projects (shared cache)"))
        try:
            project_cache = core.fetch_projects(cfg)
        except Exception as e:
            on_event(ProgressEvent("error", "Projects (shared cache)", message=str(e)))
            project_cache = []

    sections: list[tuple[str, int]] = []
    for c in checks:
        on_event(ProgressEvent("start", c.label))
        try:
            if c.arg == "projects":
                rows = c.fn(cfg, project_cache or [])
            else:
                rows = c.fn(cfg)
        except Exception as e:
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
