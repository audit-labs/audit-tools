"""
Collect organization identity: user entitlements and group memberships.

- user_entitlements: org members with access level (license) and last access,
  via the Member Entitlement Management API (vsaex host).
- group_memberships: who belongs to each org security group, via the identity
  graph (vssps host). Requires the PAT to have graph read scope.
"""

from .api import get, paginate, vsaex_url, vssps_url

ENTITLEMENTS_API = "7.1-preview.3"
GRAPH_API = "7.1-preview.1"


def user_entitlements(cfg):
    """One row per organization member: access level, status, last access."""
    rows = []
    url = vsaex_url(cfg, "_apis/userentitlements")
    params = {"api-version": ENTITLEMENTS_API, "$top": 100}
    while True:
        data = get(url, cfg, params).json()
        # This API returns "members" (paged) or "value"; support both.
        members = data.get("members") or data.get("value") or []
        for m in members:
            user = m.get("user", {})
            access = m.get("accessLevel", {})
            rows.append(
                {
                    "user": user.get("mailAddress") or user.get("principalName", ""),
                    "display_name": user.get("displayName", ""),
                    "access_level": access.get("licenseDisplayName", ""),
                    "status": access.get("status", ""),
                    "last_accessed": m.get("lastAccessedDate", ""),
                }
            )
        token = data.get("continuationToken")
        if not token:
            break
        params["continuationToken"] = token
    return rows


def group_memberships(cfg):
    """One row per (group, member). Member descriptors are resolved to names."""
    users = {
        u["descriptor"]: (
            u.get("mailAddress") or u.get("principalName") or u.get("displayName", "")
        )
        for u in paginate(
            vssps_url(cfg, "_apis/graph/users"), cfg, {"api-version": GRAPH_API}
        )
    }
    groups = paginate(
        vssps_url(cfg, "_apis/graph/groups"), cfg, {"api-version": GRAPH_API}
    )
    name_of = dict(users)
    for g in groups:
        name_of[g["descriptor"]] = f"[group] {g.get('displayName', '')}"

    rows = []
    for g in groups:
        gname = g.get("displayName", "")
        members = paginate(
            vssps_url(cfg, f"_apis/graph/memberships/{g['descriptor']}"),
            cfg,
            {"direction": "down", "api-version": GRAPH_API},
        )
        for mem in members:
            desc = mem.get("memberDescriptor", "")
            rows.append(
                {
                    "group": gname,
                    "member": name_of.get(desc, desc),
                    "member_descriptor": desc,
                }
            )
    return rows
