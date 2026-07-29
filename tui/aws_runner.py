"""
Drive the AWS audit collectors from the TUI.

Reuses the collectors and CSV reporter under ``applications/aws`` unchanged.
Mirrors the other runners: a ``CHECKS`` registry plus ``run_audit`` that writes
the same package ``applications/aws/audit.py`` produces and reports progress
through a callback.

AWS collectors take a single config dict (a boto3 session plus region/account);
there is no per-item cache, so every check is called as ``fn(cfg)``.
"""

import os
import sys
from collections.abc import Iterable
from datetime import date

from tui.common import Check, ProgressCallback, ProgressEvent

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from applications.aws.collectors import api, iam, s3, sso
from applications.aws.reporters import csv_reporter

# --- Check registry ---------------------------------------------------------

CHECKS: list[Check] = [
    Check("iam_users", "IAM users", iam.iam_users, "iam_users.csv"),
    Check(
        "password_policy",
        "Password policy",
        iam.password_policy,
        "password_policy.csv",
    ),
    Check(
        "s3_public_access",
        "S3 public access",
        s3.s3_public_access,
        "s3_public_access.csv",
    ),
    Check(
        "sso_assignments",
        "SSO assignments",
        sso.sso_assignments,
        "sso_assignments.csv",
        note="requires Identity Center + Organizations",
    ),
]

DEFAULT_SELECTION = [c.key for c in CHECKS if c.key != "sso_assignments"]


# --- Output helper ----------------------------------------------------------


def default_output_dir(out: str, profile: str) -> str:
    """Match the folder naming used by applications/aws/audit.py."""
    subject = profile or "default"
    return os.path.join(out, f"aws_audit_{subject}_{date.today().isoformat()}")


# --- Runner -----------------------------------------------------------------


def run_audit(
    *,
    profile: str,
    region: str,
    account: str,
    output_dir: str,
    selected_keys: Iterable[str],
    on_event: ProgressCallback,
) -> list[tuple[str, int]]:
    """
    Run the selected checks and write the audit package to ``output_dir``.

    A collector that raises is reported as an error and recorded with a count
    of 0, so one bad check never aborts the whole run. If the AWS session itself
    can't be built (e.g. an unknown profile), that is reported and the run ends
    cleanly.
    """
    subject = profile or "default"
    selected = set(selected_keys)
    checks = [c for c in CHECKS if c.key in selected]

    try:
        cfg = api.build_cfg(profile, region, account)
    except Exception as e:
        on_event(ProgressEvent("error", "AWS session", message=str(e)))
        csv_reporter.write_summary(output_dir, subject, [])
        on_event(ProgressEvent("summary", output_dir, count=0))
        return []

    sections: list[tuple[str, int]] = []
    for c in checks:
        on_event(ProgressEvent("start", c.label))
        try:
            rows = c.fn(cfg)
        except Exception as e:
            on_event(ProgressEvent("error", c.label, message=str(e)))
            sections.append((c.label, 0))
            continue

        csv_reporter.write(output_dir, c.filename, rows)
        sections.append((c.label, len(rows)))
        on_event(ProgressEvent("done", c.label, count=len(rows)))

    csv_reporter.write_summary(output_dir, subject, sections)
    total = sum(n for _, n in sections)
    on_event(ProgressEvent("summary", output_dir, count=total))
    return sections
