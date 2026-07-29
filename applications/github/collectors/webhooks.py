"""
Collect organization and repository webhooks.

Flags webhooks that deliver over plain HTTP or with SSL verification disabled.
"""

import sys
from urllib.parse import urlparse

import requests

from .api import paginate


def webhooks(org, cfg):
    rows = [
        _hook_row("org", h)
        for h in paginate(f"https://api.github.com/orgs/{org}/hooks", cfg)
    ]

    for repo in paginate(f"https://api.github.com/orgs/{org}/repos", cfg):
        name = repo["name"]
        try:
            hooks = paginate(f"https://api.github.com/repos/{org}/{name}/hooks", cfg)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                print(
                    f"  Skipping {name}: hooks endpoint returned "
                    f"{e.response.status_code}",
                    file=sys.stderr,
                )
                continue
            raise
        rows.extend(_hook_row(f"repo:{name}", h) for h in hooks)

    return rows


def _hook_row(scope, hook):
    config = hook.get("config", {})
    url = config.get("url", "")
    return {
        "scope": scope,
        "url": url,
        "insecure_url": urlparse(url).scheme == "http",
        "ssl_verification": "disabled"
        if str(config.get("insecure_ssl", "0")) == "1"
        else "enabled",
        "content_type": config.get("content_type", ""),
        "events": ", ".join(hook.get("events", [])),
        "active": hook.get("active"),
    }
