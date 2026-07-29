"""Collect deploy keys across all repositories in an org."""

import sys

import requests

from .api import paginate


def deploy_keys(org, cfg):
    rows = []
    for repo in paginate(f"https://api.github.com/orgs/{org}/repos", cfg):
        name = repo["name"]
        try:
            keys = paginate(f"https://api.github.com/repos/{org}/{name}/keys", cfg)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                print(
                    f"  Skipping {name}: keys endpoint returned "
                    f"{e.response.status_code}",
                    file=sys.stderr,
                )
                continue
            raise
        for k in keys:
            rows.append(
                {
                    "repo": name,
                    "title": k.get("title", ""),
                    "read_only": k.get("read_only"),
                    "created_at": k.get("created_at", ""),
                    "last_used": k.get("last_used") or "",
                    "added_by": k.get("added_by") or "",
                }
            )
    return rows
