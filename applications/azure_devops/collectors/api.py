"""
Shared Azure DevOps REST helpers.

Auth is a Personal Access Token sent as HTTP Basic (empty username). Azure
DevOps Services spreads its APIs across a few hostnames derived from the base
URL:

- core / git / policy / pipelines : https://dev.azure.com/{org}
- member entitlements             : https://vsaex.dev.azure.com/{org}
- identity graph                  : https://vssps.dev.azure.com/{org}

For Azure DevOps Server (on-prem) the base URL is the collection URL and the
specialized hosts don't apply; those collectors are best-effort there.
"""

import base64
import sys

import requests

DEFAULT_BASE_URL = "https://dev.azure.com"


def build_cfg(org, pat, base_url=DEFAULT_BASE_URL):
    """Build the config dict the collectors expect."""
    token = base64.b64encode(f":{pat}".encode()).decode()
    return {
        "org": org,
        "base_url": base_url.rstrip("/"),
        "headers": {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
        },
        "timeout": 30,
    }


def _host(cfg, sub):
    """Return the base URL for a sub-host (e.g. 'vsaex'), for cloud orgs."""
    base = cfg["base_url"]
    if sub and "dev.azure.com" in base:
        return base.replace("https://dev.azure.com", f"https://{sub}.dev.azure.com")
    return base


def core_url(cfg, path):
    return f"{cfg['base_url']}/{cfg['org']}/{path}"


def vsaex_url(cfg, path):
    return f"{_host(cfg, 'vsaex')}/{cfg['org']}/{path}"


def vssps_url(cfg, path):
    return f"{_host(cfg, 'vssps')}/{cfg['org']}/{path}"


def get(url, cfg, params=None):
    resp = requests.get(
        url, headers=cfg["headers"], params=params, timeout=cfg["timeout"]
    )
    resp.raise_for_status()
    return resp


def paginate(url, cfg, params=None):
    """
    Fetch all items from a list endpoint that returns ``{"value": [...]}`` and
    signals more pages via the ``x-ms-continuationtoken`` response header.
    """
    results = []
    p = dict(params or {})
    while True:
        resp = get(url, cfg, p)
        results.extend(resp.json().get("value", []))
        token = resp.headers.get("x-ms-continuationtoken")
        if not token:
            break
        p["continuationToken"] = token
    return results


def safe_paginate(url, cfg, params, context):
    """paginate(), but skip a resource that returns 403/404 with a warning."""
    try:
        return paginate(url, cfg, params)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            print(
                f"  Skipping {context}: returned {e.response.status_code}",
                file=sys.stderr,
            )
            return []
        raise
