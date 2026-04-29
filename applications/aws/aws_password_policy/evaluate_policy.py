#!/usr/bin/env python3
"""Evaluate AWS IAM password policy JSON and emit standardized outputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Optional
from shared.python.cli import add_standard_flags
from shared.python.logging import configure_logger
from shared.python.metadata import build_metadata
from shared.python.outputs import ensure_run_tree

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

POLICY_FIELDS = [
    (1, "MinimumPasswordLength", "Minimum password length", "int"),
    (2, "RequireSymbols", "Require symbols (!@#$…)", "bool"),
    (3, "RequireNumbers", "Require numbers (0-9)", "bool"),
    (4, "RequireUppercaseCharacters", "Require uppercase letters (A-Z)", "bool"),
    (5, "RequireLowercaseCharacters", "Require lowercase letters (a-z)", "bool"),
    (6, "AllowUsersToChangePassword", "Allow users to change password", "bool"),
    (7, "ExpirePasswords", "Expire passwords (enable aging)", "bool"),
    (8, "MaxPasswordAge", "Maximum password age (days)", "int"),
    (9, "PasswordReusePrevention", "Prevent password reuse (last N)", "int"),
    (10, "HardExpiry", "Hard expiry (no grace period)", "bool"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate IAM password policy report.")
    parser.add_argument("policy_report", help="Path to JSON file produced by gather_policy.sh")
    add_standard_flags(parser, formats=("csv", "json", "txt"))
    return parser.parse_args()


def prompt_expected(field_type: str, description: str) -> Optional[Any]:
    while True:
        raw = input(f"Enter expected value for '{description}' ({field_type}) or press <Enter> to skip: ").strip()
        if raw == "":
            return None
        if field_type == "int" and raw.isdigit():
            return int(raw)
        if field_type == "bool":
            lowered = raw.lower()
            if lowered in {"true", "t", "yes", "y", "1"}:
                return True
            if lowered in {"false", "f", "no", "n", "0"}:
                return False
        print("Invalid value; enter integer, yes/no, or leave blank.")


def evaluate(expect: Optional[Any], actual: Any, field_type: str) -> str:
    if expect is None:
        return "N/A"
    if field_type == "int":
        return "PASS" if isinstance(actual, int) and actual >= expect else "FAIL"
    if field_type == "bool":
        return "PASS" if actual is expect else "FAIL"
    return "FAIL"


def main() -> int:
    args = parse_args()
    logger = configure_logger("aws_password_policy.evaluate", verbose=args.verbose, quiet=args.quiet)

    policy_path = Path(args.policy_report)
    if not policy_path.exists():
        logger.error("Policy input not found: %s", policy_path)
        return 2

    run_paths = ensure_run_tree(args.output_dir, "aws_password_policy")
    run_id = run_paths["root"].name

    try:
        data = json.loads(policy_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Could not read JSON file %s: %s", policy_path, exc)
        return 20

    metadata_src = data.get("metadata", {})
    policy = data.get("PasswordPolicy", {})

    print("\n=== Expected / Minimum Values (press <Enter> for N/A) ===\n")
    expectations: dict[str, Optional[Any]] = {}
    for _, key, friendly, typ in POLICY_FIELDS:
        expectations[key] = prompt_expected(typ, friendly)

    csv_rows: list[list[Any]] = []
    for rule_no, key, friendly, typ in POLICY_FIELDS:
        expected = expectations[key]
        actual = policy.get(key, "(missing)")
        result = evaluate(expected, actual, typ)
        actual_str = str(actual).lower() if isinstance(actual, bool) else str(actual)
        expected_str = "" if expected is None else str(expected).lower()
        csv_rows.append([rule_no, friendly, expected_str, actual_str, result])

    if args.dry_run:
        logger.info("Dry run complete; no output files written.")
        return 0

    parsed_csv = run_paths["parsed"] / f"policy_audit_{run_id}.csv"
    with parsed_csv.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        for key, val in metadata_src.items():
            writer.writerow([f"# {key}: {val}"])
        writer.writerow([])
        writer.writerow(["Rule#", "Policy-Item", "Expected", "Actual", "Result"])
        writer.writerows(csv_rows)

    parsed_json = run_paths["parsed"] / f"policy_audit_{run_id}.json"
    parsed_json.write_text(json.dumps(csv_rows, indent=2), encoding="utf-8")

    if args.format == "csv":
        legacy_output = Path(f"policy_audit_{run_id}.csv")
        legacy_output.write_text(parsed_csv.read_text(encoding="utf-8"), encoding="utf-8")

    metadata = build_metadata(
        tool="aws_password_policy",
        run_id=run_id,
        command=" ".join(sys.argv),
        record_counts={"rules_evaluated": len(csv_rows)},
    )
    (run_paths["root"] / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    logger.info("Audit CSV written to: %s", parsed_csv)
    print("\nSummary:")
    for row in csv_rows:
        print(f"  {row[0]:2}. {row[1]:35} -> {row[4]}")
    print("\n--- End of report ---\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
