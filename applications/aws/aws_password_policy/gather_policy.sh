#!/usr/bin/env bash
#
# gather_policy.sh
# ----------------
# 1. Calls AWS CLI to fetch the current IAM password policy.
# 2. Captures execution metadata (date, user, host, AWS profile/region, etc.).
# 3. Writes a single JSON document (policy_report.json) that the Python
#    script can consume.
#
# Prerequisites:
#   • AWS CLI v2 installed and configured (credentials, default region, etc.)
#   • jq installed (used to merge JSON objects).  If jq is missing the script
#     will abort with a helpful message.
#
# Usage:
#   $ chmod +x gather_policy.sh
#   $ ./gather_policy.sh          # creates policy_report.json in the cwd
#   $ ./gather_policy.sh -o /tmp/my_report.json   # custom output path
#

set -euo pipefail

# ---------- Helper ----------
die() { echo "ERROR: $*" >&2; exit 1; }

# ---------- Argument parsing ----------
OUTFILE="policy_report.json"
while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output)
            shift
            [[ -z "${1:-}" ]] && die "Missing argument for -o|--output"
            OUTFILE="$1"
            ;;
        -h|--help)
            echo "Usage: $0 [-o|--output <path-to-json>]"
            exit 0
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
    shift
done

# ---------- Verify prerequisites ----------
command -v aws >/dev/null || die "AWS CLI not found in PATH"
command -v jq >/dev/null || die "jq not found in PATH – install it (e.g. sudo dnf install jq)"

# ---------- 1. Pull the IAM password policy ----------
# If no policy exists, AWS returns a NoSuchEntity error – we capture that
if ! POLICY_JSON=$(aws iam get-account-password-policy 2>/dev/null); then
    die "No password policy is defined for this AWS account (AWS returned NoSuchEntity)."
fi

# ---------- 2. Gather metadata ----------
#   * timestamp (UTC)
#   * OS user running the script
#   * hostname
#   * current working directory (useful for traceability)
#   * AWS profile & region (if set)
#   * AWS caller identity (ARN, account id, user id) – proves *who* ran the command
# Build with `jq --arg` so values containing quotes/backslashes (e.g. an odd
# hostname or working directory) can never produce malformed JSON.
CALLER_IDENTITY=$(aws sts get-caller-identity 2>/dev/null || echo "null")
METADATA=$(jq -n \
    --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
    --arg user "$(id -un)" \
    --arg host "$(hostname)" \
    --arg cwd "$(pwd)" \
    --arg profile "${AWS_PROFILE:-default}" \
    --arg region "${AWS_DEFAULT_REGION:-unknown}" \
    --argjson caller "$CALLER_IDENTITY" \
    '{metadata: {
        report_timestamp_utc: $ts,
        os_user: $user,
        hostname: $host,
        working_directory: $cwd,
        aws_profile: $profile,
        aws_region: $region,
        aws_caller_identity: $caller
    }}')

# ---------- 3. Merge policy + metadata ----------
# The final JSON will have two top‑level keys: "metadata" and "PasswordPolicy"
FINAL_JSON=$(jq -s 'reduce .[] as $item ({}; . * $item)' <(echo "$METADATA") <(echo "$POLICY_JSON"))

# ---------- 4. Write output ----------
echo "$FINAL_JSON" | jq '.' > "$OUTFILE"

echo "Password‑policy report written to: $OUTFILE"
