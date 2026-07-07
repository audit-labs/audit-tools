"""Human-readable reporting outputs."""

from __future__ import annotations

from pathlib import Path


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
    *,
    input_file: Path,
    input_sheet: str | None,
    input_sha256: str,
    source_row_count: int,
    options,
    effective_id_column: str | None,
    id_column_omitted: bool,
    duplicate_id_count: int,
    blank_id_count: int,
    sample_size_actual: int,
    random_seed: int | None,
    strata_summary: list[dict[str, object]] | None,
) -> str:
    lines = [
        "Audit Sampling Methodology",
        "",
        f"Source file: {input_file}",
        f"Source sheet: {input_sheet or ''}",
        f"Input SHA-256: {input_sha256}",
        f"Source row count: {source_row_count}",
    ]
    if id_column_omitted:
        lines.append(
            "ID column: omitted; _audit_row_id was generated from _source_row_number."
        )
    else:
        lines.append(f"ID column: {options.id_column}")
    lines.extend(
        [
            f"Effective ID column: {effective_id_column or ''}",
            f"Duplicate ID rows identified: {duplicate_id_count}",
            f"Blank ID rows identified: {blank_id_count}",
            f"Blank ID handling: {'excluded' if options.exclude_blank_id else 'retained'}",
            f"Filters applied: {options.filters or {}}",
            f"Sampling method: {options.method}",
            f"Sample size requested: {options.sample_size or ''}",
            f"Sample size selected: {sample_size_actual}",
            f"Random seed used: {random_seed or ''}",
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
