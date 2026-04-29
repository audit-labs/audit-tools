"""
Collect GitHub audit log events.

Requires GitHub Enterprise. Skips gracefully with a warning if not available.
"""

import sys

from .api import paginate

# Default event categories relevant to a security audit
DEFAULT_ACTIONS = [
    "org.add_member",
    "org.remove_member",
    "org.update_member",
    "protected_branch",
    "repo.access",
    "repo.create",
    "repo.destroy",
    "team.add_member",
    "team.remove_member",
]


def audit_log(org, cfg, actions=None):
    """
    Return audit log events filtered by action list.
    Returns an empty list with a warning if the org is not on GitHub Enterprise.
    """
    actions = actions or DEFAULT_ACTIONS
    url = f"https://api.github.com/orgs/{org}/audit-log"

    try:
        events = paginate(url, cfg, {"action": ",".join(actions)})
    except Exception as e:
        if "403" in str(e) or "404" in str(e):
            print(
                "Warning: audit log requires GitHub Enterprise -- skipping.",
                file=sys.stderr,
            )
            return []
        raise

    rows = []
    for e in events:
        rows.append(
            {
                "action": e.get("action", ""),
                "actor": e.get("actor", ""),
                "repo": e.get("repo", ""),
                "created_at": e.get("created_at", ""),
                "org": e.get("org", ""),
            }
        )
    return rows
