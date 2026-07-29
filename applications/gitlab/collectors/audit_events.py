"""
Collect group membership audit events (created / updated / destroyed).

Group audit events require a GitLab Premium or Ultimate subscription. Returns an
empty list with a warning if the endpoint is unavailable (403/404).
"""

import sys

import requests

from .api import enc, paginate

MEMBER_ACTIONS = {"member_created", "member_updated", "member_destroyed"}


def audit_events(group, cfg):
    try:
        events = paginate(f"{cfg['base_url']}/groups/{enc(group)}/audit_events", cfg)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            print(
                "Warning: group audit events require GitLab Premium/Ultimate and "
                "owner access -- skipping.",
                file=sys.stderr,
            )
            return []
        raise

    rows = []
    for event in events:
        action = event.get("event_name", "")
        if action not in MEMBER_ACTIONS:
            continue
        details = event.get("details", {})
        rows.append(
            {
                "created_at": event.get("created_at", ""),
                "action": action,
                "member_id": details.get("member_id", ""),
                "target": details.get("target_details", ""),
                "author_id": event.get("author_id", ""),
                "entity_type": event.get("entity_type", ""),
            }
        )
    return rows
