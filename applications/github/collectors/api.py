"""Shared GitHub API helper."""

import requests


def paginate(url, cfg, params=None):
    """Fetch all pages from a GitHub API endpoint and return combined results."""
    results = []
    p = dict(params or {})
    p["per_page"] = 100
    page = 1

    while True:
        p["page"] = page
        resp = requests.get(url, headers=cfg["headers"], params=p, timeout=cfg["timeout"])
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        results.extend(data)
        if "next" not in resp.links:
            break
        page += 1

    return results
