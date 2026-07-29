"""
AWS audit CLI.

Runs all collectors against the account reachable with the active AWS
credentials and writes a timestamped audit package to an output directory.

Credentials come from the standard AWS chain (environment variables, shared
config/credentials, SSO profiles, instance roles) — no access keys are passed
to this tool.

Usage:
    export AWS_PROFILE=my-profile          # optional
    export AWS_DEFAULT_REGION=us-east-1    # optional

    python audit.py
    python audit.py --profile my-profile --region us-east-1
    python audit.py --account my-account --out ./output

Output:
    <out>/aws_audit_<profile>_<date>/
        iam_users.csv
        password_policy.csv
        s3_public_access.csv
        sso_assignments.csv
        summary.txt
"""

import argparse
import os
import sys
from datetime import date

import config
from collectors import iam, s3, sso
from reporters import csv_reporter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an AWS audit package for the current account."
    )
    parser.add_argument(
        "--profile", help="AWS named profile. Overrides AWS_PROFILE env var."
    )
    parser.add_argument(
        "--region", help="AWS region. Overrides AWS_DEFAULT_REGION env var."
    )
    parser.add_argument(
        "--account",
        help="Account name for the SSO assignments check. "
        "Overrides AWS_AUDIT_ACCOUNT. Defaults to the current account.",
    )
    parser.add_argument(
        "--out",
        default="./output",
        help="Directory to write the audit package into. Default: ./output",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    cfg = config.load(args.profile, args.region, args.account)
    subject = cfg.get("profile") or "default"

    output_dir = os.path.join(
        args.out, f"aws_audit_{subject}_{date.today().isoformat()}"
    )

    print(f"AWS Audit — profile: {subject}")
    print(f"Output directory: {output_dir}")
    print()

    sections = []

    def collect(label, fn, filename):
        print(f"Collecting: {label}...")
        try:
            rows = fn(cfg)
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            rows = []
        csv_reporter.write(output_dir, filename, rows)
        sections.append((label, len(rows)))
        return rows

    collect("IAM users", iam.iam_users, "iam_users.csv")
    collect("Password policy", iam.password_policy, "password_policy.csv")
    collect("S3 public access", s3.s3_public_access, "s3_public_access.csv")
    collect("SSO assignments", sso.sso_assignments, "sso_assignments.csv")

    print()
    csv_reporter.write_summary(output_dir, subject, sections)
    print()
    print("Done.")


if __name__ == "__main__":
    run()
