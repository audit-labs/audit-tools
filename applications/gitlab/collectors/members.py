"""
Collect group and project membership with access levels.

GitLab access levels:
    0  No access     5  Minimal     10 Guest      15 Planner
    20 Reporter      30 Developer   40 Maintainer 50 Owner     60 Admin
"""

import sys

import requests

from .api import enc, paginate

ACCESS_LEVELS = {
    0: "No access",
    5: "Minimal",
    10: "Guest",
    15: "Planner",
    20: "Reporter",
    30: "Developer",
    40: "Maintainer",
    50: "Owner",
    60: "Admin",
}


def _role(level):
    return ACCESS_LEVELS.get(level, str(level))


def group_members(group, cfg):
    """Group members, including those inherited from parent groups."""
    members = paginate(f"{cfg['base_url']}/groups/{enc(group)}/members/all", cfg)
    return [
        {
            "username": m["username"],
            "name": m.get("name", ""),
            "access_level": m["access_level"],
            "role": _role(m["access_level"]),
            "state": m.get("state", ""),
        }
        for m in members
    ]


def project_members(group, cfg, projects):
    """Direct and inherited members of every project in the group."""
    rows = []
    for p in projects:
        try:
            members = paginate(f"{cfg['base_url']}/projects/{p['id']}/members/all", cfg)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                print(
                    f"  Skipping {p.get('path_with_namespace', p['id'])}: "
                    f"members returned {e.response.status_code}",
                    file=sys.stderr,
                )
                continue
            raise
        for m in members:
            rows.append(
                {
                    "project": p.get("path_with_namespace", ""),
                    "username": m["username"],
                    "name": m.get("name", ""),
                    "access_level": m["access_level"],
                    "role": _role(m["access_level"]),
                }
            )
    return rows
