"""Shared GitLab API helpers."""

from urllib.parse import quote

import requests

DEFAULT_BASE_URL = "https://gitlab.com/api/v4"


def enc(value):
    """URL-encode a group or project identifier.

    GitLab accepts either a numeric ID or a URL-encoded path (e.g.
    ``my-group/sub-group``). Numeric IDs pass through unchanged.
    """
    return quote(str(value), safe="")


def paginate(url, cfg, params=None):
    """Fetch all pages from a GitLab endpoint using the X-Next-Page header."""
    results = []
    p = dict(params or {})
    p["per_page"] = 100
    page = 1

    while True:
        p["page"] = page
        resp = requests.get(
            url, headers=cfg["headers"], params=p, timeout=cfg["timeout"]
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        results.extend(data)
        next_page = resp.headers.get("X-Next-Page")
        if not next_page:
            break
        page = int(next_page)

    return results
