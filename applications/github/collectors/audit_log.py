"""
Collect GitHub audit log events.

Requires GitHub Enterprise Cloud. Skips gracefully with a warning if not
available.
"""

from datetime import date, datetime, timezone, timedelta
import json
import sys

import requests

# GitHub audit logs retain non-Git events for 180 days. Supplying a created:
# qualifier is required to get events older than the default three-month window.
DEFAULT_LOOKBACK_DAYS = 180
DEFAULT_ACTION_FAMILIES = ["protected_branch", "repository_ruleset"]
DETAIL_FIELDS = [
    "name",
    "old_name",
    "branch",
    "repo",
    "repository",
    "operation_type",
    "ruleset_id",
    "ruleset_name",
    "ruleset_old_name",
    "ruleset_enforcement",
    "ruleset_old_enforcement",
    "ruleset_source_type",
    "ruleset_bypass_actors",
    "ruleset_bypass_actors_added",
    "ruleset_bypass_actors_deleted",
    "ruleset_bypass_actors_updated",
    "ruleset_conditions",
    "ruleset_conditions_added",
    "ruleset_conditions_deleted",
    "ruleset_conditions_updated",
    "ruleset_rules",
    "ruleset_rules_added",
    "ruleset_rules_deleted",
    "ruleset_rules_updated",
    "required_status_checks_enforcement_level",
    "strict_required_status_checks_policy",
    "pull_request_reviews_enforcement_level",
    "required_approving_review_count",
    "require_code_owner_review",
    "require_last_push_approval",
    "admin_enforced",
    "allow_force_pushes_enforcement_level",
    "allow_deletions_enforcement_level",
    "lock_branch_enforcement_level",
    "linear_history_requirement_enforcement_level",
    "signature_requirement_enforcement_level",
    "merge_queue_enforcement_level",
]


def audit_log(org, cfg, actions=None, lookback_days=DEFAULT_LOOKBACK_DAYS):
    """
    Return branch protection and repository ruleset audit events.

    Returns an empty list with a warning if the org is not on GitHub Enterprise
    Cloud or the token does not have audit-log access.
    """
    action_families = actions or DEFAULT_ACTION_FAMILIES
    url = f"https://api.github.com/orgs/{org}/audit-log"
    since = date.today() - timedelta(days=lookback_days)

    try:
        events = []
        for action_family in action_families:
            params = {
                "phrase": f"action:{action_family} created:>={since.isoformat()}",
                "include": "web",
                "order": "desc",
                "per_page": 100,
            }
            events.extend(_paginate_audit_log(url, cfg, params))
    except Exception as e:
        if "403" in str(e) or "404" in str(e):
            print(
                "Warning: audit log requires GitHub Enterprise Cloud, organization owner access, and audit-log token permissions -- skipping.",
                file=sys.stderr,
            )
            return []
        raise

    rows = []
    for e in _dedupe_events(events):
        rows.append(
            {
                "action": e.get("action", ""),
                "actor": e.get("actor", ""),
                "repo": e.get("repo", ""),
                "branch_or_pattern": _branch_or_pattern(e),
                "operation_type": e.get("operation_type", ""),
                "summary": _event_summary(e),
                "details": _event_details(e),
                "created_at": _format_created_at(e.get("created_at", "")),
                "org": e.get("org", ""),
            }
        )
    return rows


def _paginate_audit_log(url, cfg, params):
    """Fetch all audit-log cursor pages by following GitHub's Link header."""
    results = []
    next_url = url
    next_params = params

    while next_url:
        resp = requests.get(
            next_url,
            headers=cfg["headers"],
            params=next_params,
            timeout=cfg["timeout"],
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break

        results.extend(data)
        next_url = resp.links.get("next", {}).get("url")
        next_params = None

    return results


def _event_details(event):
    """Compact the change-specific audit-log fields into one CSV column."""
    details = {
        field: event[field]
        for field in DETAIL_FIELDS
        if field in event and event[field] not in (None, "")
    }
    return json.dumps(details, sort_keys=True)


def _dedupe_events(events):
    """Return events once, sorted newest first."""
    seen = set()
    unique = []
    for event in events:
        key = (
            event.get("@timestamp") or event.get("created_at"),
            event.get("action"),
            event.get("actor"),
            event.get("repo"),
            event.get("operation_type"),
            event.get("ruleset_id"),
            event.get("name") or event.get("ruleset_name"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return sorted(unique, key=_event_sort_value, reverse=True)


def _branch_or_pattern(event):
    """Find the most useful target label for branch and ruleset audit events."""
    return (
        event.get("name")
        or event.get("branch")
        or event.get("ruleset_name")
        or event.get("ruleset_old_name")
        or ""
    )


def _event_summary(event):
    """Build a short human-readable evidence summary for the CSV."""
    action = event.get("action", "")
    operation = event.get("operation_type", "")
    repo = event.get("repo", "")
    target = _branch_or_pattern(event)

    if action.startswith("repository_ruleset."):
        source_type = event.get("ruleset_source_type", "")
        scope = f"{source_type.lower()} " if source_type else ""
        label = f" '{target}'" if target else ""
        location = f" for {repo}" if repo else ""
        return f"{operation or action} {scope}ruleset{label}{location}".strip()

    if action.startswith("protected_branch."):
        label = f" '{target}'" if target else ""
        location = f" in {repo}" if repo else ""
        return f"{operation or action} branch protection{label}{location}".strip()

    return action


def _format_created_at(value):
    """Normalize GitHub audit-log timestamps to ISO-8601 UTC strings."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 9999999999 else value
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    return str(value)


def _event_sort_value(event):
    value = event.get("@timestamp") or event.get("created_at") or 0
    if isinstance(value, (int, float)):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0
