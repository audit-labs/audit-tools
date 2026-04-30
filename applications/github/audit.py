"""
GitHub audit CLI.

Runs all collectors against a GitHub organization and writes a timestamped
audit package to an output directory.

Usage:
    export GITHUB_TOKEN=your_token
    export GITHUB_ORG=your_org

    python audit.py
    python audit.py --org my-org
    python audit.py --org my-org --out ./output
    python audit.py --org my-org --branch main --include-audit-log

Output:
    <out>/github_audit_<org>_<date>/
        member_roster.csv
        two_factor_disabled.csv
        outside_collaborators.csv
        privileged_access.csv
        pending_invitations.csv
        team_permissions.csv
        permission_matrix.csv
        branch_protections.csv
        commits.csv
        audit_log.csv           (only with --include-audit-log)
        summary.txt
"""

import argparse
import os
import sys
from datetime import date

import config
from collectors import members, branch_protections, commits, audit_log
from reporters import csv_reporter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a GitHub audit package for an organization."
    )
    parser.add_argument(
        "--org",
        help="GitHub organization name. Overrides GITHUB_ORG env var.",
    )
    parser.add_argument(
        "--out",
        default="./output",
        help="Directory to write the audit package into. Default: ./output",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch to collect commits from. Default: main",
    )
    parser.add_argument(
        "--include-audit-log",
        action="store_true",
        help="Include audit log collection (requires GitHub Enterprise).",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    cfg = config.load(org_override=args.org)
    org = cfg["org"]

    output_dir = os.path.join(
        args.out, f"github_audit_{org}_{date.today().isoformat()}"
    )

    print(f"GitHub Audit — {org}")
    print(f"Output directory: {output_dir}")
    print()

    sections = []

    def collect(label, fn, filename, *fn_args):
        print(f"Collecting: {label}...")
        try:
            rows = fn(*fn_args)
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            rows = []
        csv_reporter.write(output_dir, filename, rows)
        sections.append((label, len(rows)))
        return rows

    collect("Member roster", members.member_roster, "member_roster.csv", org, cfg)
    collect(
        "2FA disabled", members.two_factor_disabled, "two_factor_disabled.csv", org, cfg
    )

    print("Fetching repo collaborators (shared cache)...")
    try:
        repo_collabs = members.fetch_repo_collaborators(org, cfg)
    except Exception as e:
        print(f"  Error fetching collaborators: {e}", file=sys.stderr)
        repo_collabs = []

    collect(
        "Outside collaborators",
        members.outside_collaborators,
        "outside_collaborators.csv",
        org,
        cfg,
        repo_collabs,
    )
    collect(
        "Privileged access",
        members.privileged_access,
        "privileged_access.csv",
        org,
        cfg,
        repo_collabs,
    )
    collect(
        "Pending invitations",
        members.pending_invitations,
        "pending_invitations.csv",
        org,
        cfg,
    )
    collect(
        "Team permissions", members.team_permissions, "team_permissions.csv", org, cfg
    )
    collect(
        "Permission matrix",
        members.permission_matrix,
        "permission_matrix.csv",
        org,
        cfg,
        repo_collabs,
    )
    collect(
        "Branch protections",
        branch_protections.branch_protections,
        "branch_protections.csv",
        org,
        cfg,
    )
    collect("Commits", commits.commits, "commits.csv", org, cfg, args.branch)

    if args.include_audit_log:
        collect("Audit log", audit_log.audit_log, "audit_log.csv", org, cfg)

    print()
    csv_reporter.write_summary(output_dir, org, sections)
    print()
    print("Done.")


if __name__ == "__main__":
    run()
