"""Collect protected-branch settings for every project in the group."""

import sys

import requests

from .api import paginate


def _levels(entries):
    """Summarize an access-level list (push/merge/unprotect) into one string."""
    return ", ".join(e.get("access_level_description", "") for e in entries) or "(none)"


def branch_protections(_group, cfg, projects):
    rows = []
    for p in projects:
        try:
            protected = paginate(
                f"{cfg['base_url']}/projects/{p['id']}/protected_branches", cfg
            )
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                print(
                    f"  Skipping {p.get('path_with_namespace', p['id'])}: "
                    f"protected_branches returned {e.response.status_code}",
                    file=sys.stderr,
                )
                continue
            raise
        for b in protected:
            rows.append(
                {
                    "project": p.get("path_with_namespace", ""),
                    "branch": b.get("name", ""),
                    "push_access": _levels(b.get("push_access_levels", [])),
                    "merge_access": _levels(b.get("merge_access_levels", [])),
                    "allow_force_push": b.get("allow_force_push"),
                    "code_owner_approval_required": b.get(
                        "code_owner_approval_required"
                    ),
                }
            )
    return rows
