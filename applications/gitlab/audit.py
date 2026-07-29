"""
GitLab audit CLI.

Runs all collectors against a GitLab group and writes a timestamped audit
package to an output directory.

Usage:
    export GITLAB_TOKEN=your_token
    export GITLAB_GROUP=your_group_id_or_path

    python audit.py
    python audit.py --group my-group
    python audit.py --group my-group --out ./output
    python audit.py --group my-group --url https://gitlab.example.com/api/v4

Output:
    <out>/gitlab_audit_<group>_<date>/
        group_members.csv
        projects.csv
        project_members.csv
        branch_protections.csv
        pipelines.csv
        approval_rules.csv
        audit_events.csv
        password_policy.csv
        summary.txt
"""

import argparse
import os
import sys
from datetime import date

import config
from collectors import (
    approvals,
    audit_events,
    branch_protections,
    members,
    pipelines,
    projects,
    settings,
)
from reporters import csv_reporter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a GitLab audit package for a group."
    )
    parser.add_argument(
        "--group",
        help="GitLab group ID or path. Overrides GITLAB_GROUP env var.",
    )
    parser.add_argument(
        "--url",
        help="GitLab API base URL. Overrides GITLAB_URL env var. "
        "Default: https://gitlab.com/api/v4",
    )
    parser.add_argument(
        "--out",
        default="./output",
        help="Directory to write the audit package into. Default: ./output",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    cfg = config.load(group_override=args.group, base_url_override=args.url)
    group = cfg["group"]

    safe_group = group.replace("/", "-")
    output_dir = os.path.join(
        args.out, f"gitlab_audit_{safe_group}_{date.today().isoformat()}"
    )

    print(f"GitLab Audit — {group}")
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

    print("Enumerating projects (shared cache)...")
    try:
        project_cache = projects.fetch_projects(group, cfg)
    except Exception as e:
        print(f"  Error enumerating projects: {e}", file=sys.stderr)
        project_cache = []

    collect("Group members", members.group_members, "group_members.csv", group, cfg)
    collect(
        "Projects", projects.project_list, "projects.csv", group, cfg, project_cache
    )
    collect(
        "Project members",
        members.project_members,
        "project_members.csv",
        group,
        cfg,
        project_cache,
    )
    collect(
        "Branch protections",
        branch_protections.branch_protections,
        "branch_protections.csv",
        group,
        cfg,
        project_cache,
    )
    collect(
        "Pipelines", pipelines.pipelines, "pipelines.csv", group, cfg, project_cache
    )
    collect(
        "Approval rules",
        approvals.approval_rules,
        "approval_rules.csv",
        group,
        cfg,
        project_cache,
    )
    collect("Audit events", audit_events.audit_events, "audit_events.csv", group, cfg)
    collect(
        "Password policy",
        settings.password_policy,
        "password_policy.csv",
        group,
        cfg,
    )

    print()
    csv_reporter.write_summary(output_dir, group, sections)
    print()
    print("Done.")


if __name__ == "__main__":
    run()
