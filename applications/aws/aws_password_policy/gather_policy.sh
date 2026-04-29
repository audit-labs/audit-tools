#!/usr/bin/env bash
# Gather AWS IAM password policy and write standardized outputs.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
# shellcheck source=/dev/null
source "${REPO_ROOT}/shared/shell/common.sh"

OUTPUT_DIR="outputs"
OUTFILE="policy_report.json"
VERBOSE=0
QUIET=0
DRY_RUN=0
FORMAT="json"

usage() {
  cat <<EOF
Usage: $0 [-o|--output <file>] [--output-dir <dir>] [--verbose] [--quiet] [--dry-run] [--format json]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      shift
      [[ -z "${1:-}" ]] && { log_error "Missing argument for -o|--output"; exit "$EXIT_USAGE"; }
      OUTFILE="$1"
      ;;
    --output-dir)
      shift
      OUTPUT_DIR="${1:-outputs}"
      ;;
    --verbose) VERBOSE=1 ;;
    --quiet) QUIET=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --format)
      shift
      FORMAT="${1:-json}"
      ;;
    -h|--help)
      usage
      exit "$EXIT_OK"
      ;;
    *)
      log_error "Unknown option: $1"
      usage
      exit "$EXIT_USAGE"
      ;;
  esac
  shift
done

[[ "$FORMAT" != "json" ]] && { log_error "Only --format json is supported."; exit "$EXIT_USAGE"; }

(( QUIET == 1 )) && log_info() { :; }

command -v aws >/dev/null || { log_error "AWS CLI not found in PATH"; exit "$EXIT_DEPENDENCY"; }
command -v jq >/dev/null || { log_error "jq not found in PATH"; exit "$EXIT_DEPENDENCY"; }

get_hostname() {
  if command -v hostname >/dev/null 2>&1; then
    hostname
    return
  fi

  if [[ -r /proc/sys/kernel/hostname ]]; then
    cat /proc/sys/kernel/hostname
    return
  fi

  uname -n 2>/dev/null || echo "unknown"
}

RUN_ROOT="$(ensure_run_tree "$OUTPUT_DIR" "aws_password_policy")"
RUN_ID="$(basename "$RUN_ROOT")"
RAW_FILE="${RUN_ROOT}/raw/policy_raw.json"
OUTFILE_BASENAME="$(basename "$OUTFILE")"
PARSED_FILE="${RUN_ROOT}/parsed/${OUTFILE_BASENAME}"
META_FILE="${RUN_ROOT}/metadata.json"

if (( DRY_RUN == 1 )); then
  log_info "Dry run: would fetch AWS password policy and write to ${PARSED_FILE}"
  exit "$EXIT_OK"
fi

if ! POLICY_JSON="$(aws iam get-account-password-policy 2>"${RUN_ROOT}/exceptions/aws_get_policy.err")"; then
  log_error "No password policy is defined for this AWS account."
  exit "$EXIT_COLLECTION"
fi

METADATA=$(cat <<EOF
{
  "metadata": {
    "report_timestamp_utc": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "os_user": "$(id -un)",
    "hostname": "$(get_hostname)",
    "working_directory": "$(pwd)",
    "aws_profile": "${AWS_PROFILE:-default}",
    "aws_region": "${AWS_DEFAULT_REGION:-unknown}",
    "aws_caller_identity": $(aws sts get-caller-identity 2>/dev/null || echo "null")
  }
}
EOF
)

echo "$POLICY_JSON" | jq '.' > "$RAW_FILE"
FINAL_JSON=$(jq -s 'reduce .[] as $item ({}; . * $item)' <(echo "$METADATA") <(echo "$POLICY_JSON"))
echo "$FINAL_JSON" | jq '.' > "$PARSED_FILE"
mkdir -p "$(dirname "$OUTFILE")"
cp "$PARSED_FILE" "$OUTFILE"

write_metadata "$META_FILE" "aws_password_policy" "$RUN_ID" "$0 $*"

log_info "Password-policy report written to: $PARSED_FILE"
(( VERBOSE == 1 )) && log_info "Legacy compatibility copy written to: $OUTFILE"
