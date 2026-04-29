"""
<Tool Name>

Audit purpose:
    <Short control-focused description>

Safety:
    - Read-only collection behavior
    - No credential logging

Usage examples:
    python main.py --scope <target> --output-dir ./outputs
    python main.py --scope <target> --output-dir ./outputs --format csv --verbose

Standard behavior:
    - Validates required inputs before collection
    - Writes deterministic run artifacts under outputs/<tool_name>/<run_id>/
    - Preserves raw evidence and writes normalized parsed outputs
    - Records metadata.json and logs
"""

# NOTE:
# - Load credentials from environment/config only.
# - Do not hardcode tokens, keys, or passwords.
# - Do not print secrets in stdout/stderr/log files.
