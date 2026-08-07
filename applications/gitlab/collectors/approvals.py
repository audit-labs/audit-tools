"""
Collect merge-request approval rules for every project in the group.

Approval rules require a GitLab Premium or Ultimate subscription. Projects that
return 403/404 (feature unavailable) are skipped with a warning.
"""

import sys

import requests

from .api import paginate


def approval_rules(_group, cfg, projects):
    rows = []
    for p in projects:
        try:
            rules = paginate(
                f"{cfg['base_url']}/projects/{p['id']}/approval_rules", cfg
            )
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                print(
                    f"  Skipping {p.get('path_with_namespace', p['id'])}: "
                    f"approval_rules returned {e.response.status_code}",
                    file=sys.stderr,
                )
                continue
            raise
        for rule in rules:
            approvers = ", ".join(
                a.get("name", "") for a in rule.get("eligible_approvers", [])
            )
            branches = ", ".join(
                b.get("name", "") for b in rule.get("protected_branches", [])
            )
            rows.append(
                {
                    "project": p.get("path_with_namespace", ""),
                    "rule": rule.get("name", ""),
                    "rule_type": rule.get("rule_type", ""),
                    "approvals_required": rule.get("approvals_required", 0),
                    "protected_branches": branches or "(all)",
                    "eligible_approvers": approvers or "(none)",
                }
            )
    return rows
