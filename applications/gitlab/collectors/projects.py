"""
Enumerate the projects in a GitLab group.

fetch_projects() returns the raw project objects once; the per-project
collectors reuse that cache to avoid re-listing the group.
"""

from .api import enc, paginate


def fetch_projects(group, cfg):
    """List all projects in the group, including subgroups."""
    return paginate(
        f"{cfg['base_url']}/groups/{enc(group)}/projects",
        cfg,
        {"include_subgroups": "true", "archived": "false"},
    )


def project_list(_group, _cfg, projects):
    """Format the project cache into audit rows."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "path": p.get("path_with_namespace", ""),
            "visibility": p.get("visibility", ""),
            "default_branch": p.get("default_branch", ""),
            "archived": p.get("archived", False),
            "web_url": p.get("web_url", ""),
        }
        for p in projects
    ]
