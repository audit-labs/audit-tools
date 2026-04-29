# Output Tree Example

Use this output structure for each tool run.

```text
outputs/
  github_org_audit/
    github_org_audit_acme_20260429T141530Z/
      raw/
        repos_page_1.json
        repos_page_2.json
      parsed/
        member_roster.csv
        branch_protections.csv
      exceptions/
        api_denials.json
      evidence/
        summary.md
      logs/
        run.log
      metadata.json
```

## Practical Notes
- `raw/` should contain unmodified source evidence.
- `parsed/` should contain normalized analysis-ready outputs.
- `exceptions/` should contain incomplete, denied, or failed records.
- `evidence/` should contain auditor-readable summaries.
- `logs/` should contain operational run logs only (no secrets).
- `metadata.json` should document run scope, command, timestamps, and counts.
