"""
Enumerate the projects in an Azure DevOps organization.

fetch_projects() returns the raw project objects once; the per-project
collectors reuse that cache.
"""

from .api import core_url, paginate

API_VERSION = "7.1"


def fetch_projects(cfg):
    return paginate(core_url(cfg, "_apis/projects"), cfg, {"api-version": API_VERSION})


def project_list(_cfg, projects):
    # _cfg is unused; project_list only formats the shared cache, but keeps the
    # uniform (cfg, projects) signature the runner dispatches "projects" checks
    # with.
    return [
        {
            "id": p["id"],
            "name": p.get("name", ""),
            "visibility": p.get("visibility", ""),
            "state": p.get("state", ""),
            "last_update": p.get("lastUpdateTime", ""),
        }
        for p in projects
    ]
