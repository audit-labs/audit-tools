"""
Collect pipeline service connections for every project.

Service connections (service endpoints) hold credentials that pipelines use to
reach external systems (Azure, registries, etc.); over-shared or over-scoped
connections are a common finding.
"""

from .api import core_url, safe_paginate

API_VERSION = "7.1-preview.4"


def service_connections(cfg, projects):
    rows = []
    for p in projects:
        endpoints = safe_paginate(
            core_url(cfg, f"{p['id']}/_apis/serviceendpoint/endpoints"),
            cfg,
            {"api-version": API_VERSION},
            f"{p.get('name', p['id'])} service connections",
        )
        for e in endpoints:
            rows.append(
                {
                    "project": p.get("name", ""),
                    "name": e.get("name", ""),
                    "type": e.get("type", ""),
                    "shared": e.get("isShared", False),
                    "auth_scheme": e.get("authorization", {}).get("scheme", ""),
                    "url": e.get("url", ""),
                }
            )
    return rows
