# <Tool Name>

## Audit Purpose
Describe the control objective, risk addressed, and why this evidence matters in
an audit.

## What This Tool Collects
- **Raw evidence:**
- **Parsed evidence:**
- **Exception evidence:**

## Prerequisites
- Access/role requirements:
- API permissions/scopes:
- Local dependencies:

## Inputs and Scope
- Required scope input(s):
- Optional date range:
- Assumptions/limitations:

## Usage
```bash
# Basic run
python main.py --scope <target> --output-dir ./outputs

# Example with JSON output and verbose logs
python main.py --scope <target> --output-dir ./outputs --format json --verbose
```

## Standard Output Model
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

## Parsed Output Schema
| Field | Type | Description |
|---|---|---|
| <field_name> | <string/int/bool> | <what it means> |

## Evidence Defensibility Notes
- State what was not collected and why.
- Preserve raw source data for re-performance.
- Document filters/scope in metadata.

## Known Limitations
- API tier gaps:
- Data blind spots:
- Runtime caveats:

## Validation / Reperformance
- Re-run command used:
- Expected artifacts:
- Manual verification steps:
