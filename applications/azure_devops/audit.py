"""
Azure DevOps audit CLI.

Runs all collectors against an Azure DevOps organization and writes a
timestamped audit package to an output directory.

The PAT is read from AZDO_PAT (environment only, never a command-line flag).

Usage:
    export AZDO_ORG=my-org
    export AZDO_PAT=your_pat

    python audit.py
    python audit.py --org my-org --out ./output
    python audit.py --url https://azuredevops.example.com/DefaultCollection

Output:
    <out>/azure_devops_audit_<org>_<date>/
        projects.csv
        user_entitlements.csv
        group_memberships.csv
        repositories.csv
        branch_policies.csv
        service_connections.csv
        summary.txt
"""

import argparse
import os
import sys
from datetime import date

import config
from collectors import core, identity, pipelines, repos
from reporters import csv_reporter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an Azure DevOps audit package for an organization."
    )
    parser.add_argument(
        "--org", help="Azure DevOps organization. Overrides AZDO_ORG env var."
    )
    parser.add_argument(
        "--url",
        help="Base URL for Azure DevOps Server. Overrides AZDO_URL. "
        "Default: https://dev.azure.com",
    )
    parser.add_argument(
        "--out",
        default="./output",
        help="Directory to write the audit package into. Default: ./output",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    cfg = config.load(org_override=args.org, base_url_override=args.url)
    org = cfg["org"]

    safe_org = org.replace("/", "-")
    output_dir = os.path.join(
        args.out, f"azure_devops_audit_{safe_org}_{date.today().isoformat()}"
    )

    print(f"Azure DevOps Audit — {org}")
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
        project_cache = core.fetch_projects(cfg)
    except Exception as e:
        print(f"  Error enumerating projects: {e}", file=sys.stderr)
        project_cache = []

    collect("Projects", core.project_list, "projects.csv", cfg, project_cache)
    collect(
        "User entitlements",
        identity.user_entitlements,
        "user_entitlements.csv",
        cfg,
    )
    collect(
        "Group memberships",
        identity.group_memberships,
        "group_memberships.csv",
        cfg,
    )
    collect("Repositories", repos.repositories, "repositories.csv", cfg, project_cache)
    collect(
        "Branch policies",
        repos.branch_policies,
        "branch_policies.csv",
        cfg,
        project_cache,
    )
    collect(
        "Service connections",
        pipelines.service_connections,
        "service_connections.csv",
        cfg,
        project_cache,
    )

    print()
    csv_reporter.write_summary(output_dir, org, sections)
    print()
    print("Done.")


if __name__ == "__main__":
    run()
