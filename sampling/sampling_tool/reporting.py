"""Human-readable reporting outputs."""

from __future__ import annotations

from pathlib import Path

from .facts import RunFacts


class RunLogger:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def log(self, message: str) -> None:
        self.lines.append(message)

    def warning(self, message: str) -> None:
        self.log(f"WARNING: {message}")

    def error(self, message: str) -> None:
        self.log(f"ERROR: {message}")

    def write(self, path: Path) -> None:
        path.write_text("\n".join(self.lines) + "\n")


def build_methodology(
    facts: RunFacts, strata_summary: list[dict[str, object]] | None
) -> str:
    options = facts.options
    lines = [
        "Audit Sampling Methodology",
        "",
        f"Source file: {facts.input_file}",
        f"Source sheet: {facts.input_sheet or ''}",
        f"Input SHA-256: {facts.input_sha256}",
        f"Source row count: {facts.source_row_count}",
    ]
    if facts.id_column_omitted:
        lines.append(
            "ID column: omitted; _audit_row_id was generated from _source_row_number."
        )
    else:
        lines.append(f"ID column: {options.id_column}")
    lines.extend(
        [
            f"Effective ID column: {facts.effective_id_column or ''}",
            f"Duplicate ID rows identified: {facts.duplicate_id_count}",
            f"Blank ID rows identified: {facts.blank_id_count}",
            f"Blank ID handling: {'excluded' if options.exclude_blank_id else 'retained'}",
            f"Filters applied: {options.filters or {}}",
            f"Sampling method: {options.method}",
            f"Sample size requested: {options.sample_size or ''}",
            f"Sample size selected: {facts.sample_size_actual}",
            f"Random seed used: {facts.random_seed or ''}",
        ]
    )
    if options.method == "stratified":
        lines.append(f"Stratification column: {options.stratify_column}")
        lines.append(f"Strata counts: {options.strata_counts or ''}")
        lines.append(f"Strata proportions: {options.strata_proportions or ''}")
        if strata_summary:
            lines.append("Strata summary:")
            for row in strata_summary:
                lines.append(
                    "  "
                    f"{row['Stratum']}: population={row['Population Count']}, "
                    f"requested={row['Requested Sample Count']}, "
                    f"actual={row['Actual Sample Count']}, "
                    f"shortfall={row['Shortfall']}"
                )
    lines.extend(
        [
            "Sampling was performed without replacement.",
            "Selected rows retain source row numbers and original source fields.",
        ]
    )
    return "\n".join(lines) + "\n"
