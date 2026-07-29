"""Collect CI/CD pipeline history for every project in the group."""

import sys

import requests

from .api import paginate


def pipelines(group, cfg, projects):
    rows = []
    for p in projects:
        try:
            project_pipelines = paginate(
                f"{cfg['base_url']}/projects/{p['id']}/pipelines", cfg
            )
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                print(
                    f"  Skipping {p.get('path_with_namespace', p['id'])}: "
                    f"pipelines returned {e.response.status_code}",
                    file=sys.stderr,
                )
                continue
            raise
        for pipe in project_pipelines:
            rows.append(
                {
                    "project": p.get("path_with_namespace", ""),
                    "pipeline_id": pipe.get("id"),
                    "status": pipe.get("status", ""),
                    "ref": pipe.get("ref", ""),
                    "source": pipe.get("source", ""),
                    "created_at": pipe.get("created_at", ""),
                    "web_url": pipe.get("web_url", ""),
                }
            )
    return rows
