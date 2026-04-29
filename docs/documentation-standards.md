# Documentation Standards

## Root README standard
Create/maintain a canonical `README` with:
1. Purpose and intended audit use cases.
2. Repository map by domain.
3. Quick-start (dependencies, auth setup, first run).
4. Safety/security notice (read-only, no secrets in outputs).
5. Output model summary.
6. Contribution workflow and coding standards links.

## Per-tool README structure
Each tool directory should include `README` with:
1. **Audit purpose** (control objective and why it matters).
2. **Evidence produced** (raw, parsed, exceptions).
3. **Prerequisites** (permissions, APIs, binaries).
4. **Inputs and scope** (required identifiers, time bounds).
5. **Usage examples** (minimal + advanced).
6. **Output schema** (columns/fields and definitions).
7. **Known limitations** (API tier limits, blind spots).
8. **Validation/re-performance steps**.

## Sample output documentation
- Provide small sanitized samples under a `samples/` sub-folder per tool.
- Include `samples/README.md` mapping sample files to schemas.
- Keep samples deterministic and non-sensitive.

## Documentation style conventions
- Prefer plain, auditor-friendly language over implementation jargon.
- Explicitly call out what was **not** collected and why.
- Include date/time format and timezone assumptions (UTC by default).
- Document expected error scenarios and remediation.

## Control-area mapping guidance
For each tool README, include a mini table:
- `control_area`
- `risk_addressed`
- `evidence_type`
- `primary_output_file`

This keeps tools aligned with audit objectives rather than only technical
output.
