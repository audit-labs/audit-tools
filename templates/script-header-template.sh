#!/usr/bin/env bash
# <Tool Name>
#
# Audit purpose:
#   <Short control-focused description>
#
# Safety:
#   - Read-only collection behavior
#   - No credential logging
#
# Usage examples:
#   ./run.sh --scope <target> --output-dir ./outputs
#   ./run.sh --scope <target> --output-dir ./outputs --format json --verbose
#
# Standard behavior:
#   - Validate required inputs before collection
#   - Write deterministic run artifacts under outputs/<tool_name>/<run_id>/
#   - Preserve raw evidence and write normalized parsed outputs
#   - Record metadata.json and logs
#
# NOTE:
# - Load credentials from environment/config only.
# - Never hardcode tokens, keys, or passwords.
# - Never print secrets in stdout/stderr/log files.
