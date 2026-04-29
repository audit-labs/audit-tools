#!/usr/bin/env bash
# Shared shell helpers for standardized evidence collection scripts.

set -o errexit
set -o nounset
set -o pipefail

EXIT_OK=0
EXIT_USAGE=2
EXIT_AUTH=10
EXIT_VALIDATION=11
EXIT_DEPENDENCY=12
EXIT_COLLECTION=20
EXIT_PARSE=21
EXIT_OUTPUT=22
EXIT_PARTIAL=30
EXIT_UNKNOWN=99

log_info() { printf '%s INFO %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
log_warn() { printf '%s WARN %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2; }
log_error() { printf '%s ERROR %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2; }

generate_run_id() { date -u +%Y%m%dT%H%M%SZ; }

ensure_run_tree() {
  local output_dir="$1"
  local tool_name="$2"
  local run_id="${3:-$(generate_run_id)}"
  local run_root="${output_dir%/}/${tool_name}/${run_id}"

  mkdir -p "${run_root}/raw" "${run_root}/parsed" "${run_root}/exceptions" "${run_root}/evidence" "${run_root}/logs"
  printf '%s\n' "$run_root"
}

write_metadata() {
  local metadata_file="$1"
  local tool="$2"
  local run_id="$3"
  local command="$4"
  python3 - "$tool" "$run_id" "$command" > "$metadata_file" <<'PY'
import json
import sys
from datetime import datetime, timezone

tool, run_id, command = sys.argv[1], sys.argv[2], sys.argv[3]
payload = {
    "tool": tool,
    "run_id": run_id,
    "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "command": command,
}
print(json.dumps(payload, indent=2))
PY
}
