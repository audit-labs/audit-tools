# Output, Schema, Metadata, and Evidence Standards

## Standard output directory model

```text
outputs/
  <tool_name>/
    <run_id>/
      raw/
      parsed/
      exceptions/
      evidence/
      logs/
      metadata.json
```

## Run ID standard
- Format: `<tool_name>_<target_scope>_<YYYYMMDDTHHMMSSZ>`
- Example: `github_org_audit_acme_20260429T141530Z`
- Must be deterministic per run invocation timestamp.

## Folder intent
- `raw/`: unmodified API responses, command output, source extracts.
- `parsed/`: normalized CSV/JSON for analysis.
- `exceptions/`: records that need manual follow-up (missing fields, API
  denials, parse failures).
- `evidence/`: auditor-facing summary artifacts (tables, narrative notes,
  screenshots if relevant).
- `logs/`: operational logs.

## CSV/JSON schema conventions
- Use lowercase `snake_case` column keys.
- Include stable unique keys where possible (`record_id`, `source_id`).
- Add `source_system`, `collected_at`, and `tool_name` for traceability in
  parsed outputs.
- Nulls should be explicit (`""` in CSV, `null` in JSON).

## Evidence metadata schema (`metadata.json`)

Required fields:
- `tool_name`
- `tool_version`
- `run_id`
- `run_started_at`
- `run_completed_at`
- `system_type`
- `target_scope`
- `command`
- `user_context`
- `hostname`
- `source_files`
- `output_files`
- `record_counts`
- `warnings`
- `errors`
- `credential_fields_redacted`
- `schema_version`

Recommended fields:
- `git_commit`
- `script_path`
- `dependencies`
- `api_rate_limit_observed`

## Example `metadata.json`
```json
{
  "tool_name": "github_org_audit",
  "tool_version": "0.2.0",
  "run_id": "github_org_audit_acme_20260429T141530Z",
  "run_started_at": "2026-04-29T14:15:30Z",
  "run_completed_at": "2026-04-29T14:17:05Z",
  "system_type": "github",
  "target_scope": "org:acme",
  "command": "python main.py --scope acme --output-dir ./outputs",
  "user_context": "local_user",
  "hostname": "audit-host-01",
  "source_files": ["raw/repos_page_1.json"],
  "output_files": ["parsed/member_roster.csv"],
  "record_counts": {"member_roster": 254},
  "warnings": [],
  "errors": [],
  "credential_fields_redacted": ["authorization_header"],
  "schema_version": "1.0.0"
}
```

## Audit defensibility requirements
- Preserve raw evidence to permit re-performance.
- Keep parsed outputs reproducible from raw inputs.
- Track command and scope exactly.
- Separate exceptions from compliant/normal records.
- Never overwrite prior runs; each run gets its own folder.
