"""CLI orchestration for the audit sampling tool."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import sys

import pandas as pd

from .filters import apply_filters, parse_filters
from .io import AuditSamplingError, load_population, sha256_file, write_csv
from .manifest import build_manifest, write_manifest
from .methods import (
    ensure_seed,
    largest_remainder_allocation,
    random_sample,
    stratified_sample,
)
from .reconciliation import build_reconciliation, build_strata_summary
from .reporting import RunLogger, build_methodology
from .validation import validate_and_prepare


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Generate documented audit samples.")
    parser.add_argument("--input")
    parser.add_argument("--sheet")
    parser.add_argument("--id-column")
    parser.add_argument("--method", choices=["random", "stratified", "validate-only"])
    parser.add_argument("--sample-size", type=int)
    parser.add_argument("--stratify-column")
    parser.add_argument("--strata-counts")
    parser.add_argument("--strata-proportions")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--out")
    parser.add_argument("--exclude-blank-id", action="store_true", default=None)
    parser.add_argument("--dedupe-id", choices=["fail", "first", "last"])
    parser.add_argument("--filter", action="append", dest="filter_values")
    parser.add_argument("--config")
    parser.add_argument("--allow-shortfall", action="store_true", default=None)
    return parser


def load_config(path: str | None) -> dict[str, object]:
    if not path:
        return {}
    try:
        import yaml
    except ImportError as exc:
        raise AuditSamplingError(
            "YAML config support requires PyYAML. Install requirements.txt."
        ) from exc

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise AuditSamplingError("Config file must contain a YAML mapping.")
    return data


def merge_options(args: Namespace, config: dict[str, object]) -> SimpleNamespace:
    mapping = {
        "input": "input",
        "sheet": "sheet",
        "id_column": "id_column",
        "method": "method",
        "sample_size": "sample_size",
        "stratify_column": "stratify_column",
        "strata_counts": "strata_counts",
        "strata_proportions": "strata_proportions",
        "seed": "seed",
        "out": "out",
        "exclude_blank_id": "exclude_blank_id",
        "dedupe_id": "dedupe_id",
        "allow_shortfall": "allow_shortfall",
    }
    merged: dict[str, object] = {}
    for attr, key in mapping.items():
        cli_value = getattr(args, attr)
        merged[attr] = cli_value if cli_value is not None else config.get(key)

    config_filters = config.get("filters", {})
    if isinstance(config_filters, list):
        config_filters = parse_filters(config_filters)
    if not isinstance(config_filters, dict):
        raise AuditSamplingError("Config filters must be a mapping or list.")
    cli_filters = parse_filters(args.filter_values)
    merged["filters"] = {**config_filters, **cli_filters}

    merged["out"] = merged["out"] or "./output"
    merged["dedupe_id"] = merged["dedupe_id"] or "fail"
    merged["exclude_blank_id"] = bool(merged["exclude_blank_id"])
    merged["allow_shortfall"] = bool(merged["allow_shortfall"])
    if merged["input"] is None:
        raise AuditSamplingError("--input is required unless provided by --config.")
    if merged["method"] is None:
        raise AuditSamplingError("--method is required unless provided by --config.")
    if merged["method"] not in {"random", "stratified", "validate-only"}:
        raise AuditSamplingError("--method must be random, stratified, or validate-only.")
    if merged["sample_size"] is not None:
        merged["sample_size"] = int(merged["sample_size"])
    if merged["seed"] is not None:
        merged["seed"] = int(merged["seed"])
    return SimpleNamespace(**merged)


def create_run_dir(out_dir: Path, now: datetime) -> Path:
    run_dir = out_dir / f"sample_{now.strftime('%Y-%m-%d_%H%M%S')}"
    suffix = 1
    while True:
        candidate = run_dir if suffix == 1 else out_dir / f"{run_dir.name}_{suffix}"
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        except FileExistsError:
            suffix += 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        options = merge_options(args, load_config(args.config))
        run(options)
        return 0
    except AuditSamplingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def run(options) -> Path:
    now = datetime.now(timezone.utc)
    timestamp = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_dir = create_run_dir(Path(options.out), now)
    logger = RunLogger()
    logger.log(f"start timestamp: {timestamp}")
    logger.log(f"input path: {options.input}")
    logger.log(f"method: {options.method}")
    logger.log(f"output folder: {run_dir}")
    print(f"Writing audit sample package to {run_dir}")

    output_files: list[str] = []
    input_path = Path(options.input)
    input_hash = ""
    source = pd.DataFrame()
    filtered = pd.DataFrame()
    validated = pd.DataFrame()
    excluded_rows = pd.DataFrame()
    duplicate_rows = pd.DataFrame()
    sample = pd.DataFrame()
    strata_rows: list[dict[str, object]] = []
    random_seed: int | None = options.seed
    effective_id_column = None
    id_column_omitted = False
    blank_id_count = 0
    duplicate_id_count = 0

    try:
        input_hash = sha256_file(input_path)
        source = load_population(input_path, options.sheet)
        filtered, filter_excluded = apply_filters(source, options.filters)
        validated = filtered.copy()
        excluded_rows = filter_excluded.copy()
        validation = validate_and_prepare(filtered, options)
        validated = validation.population
        excluded_rows = _concat_nonempty([filter_excluded, validation.excluded_rows])
        duplicate_rows = validation.duplicate_rows
        effective_id_column = validation.effective_id_column
        id_column_omitted = validation.id_column_omitted
        blank_id_count = validation.blank_id_count
        duplicate_id_count = validation.duplicate_id_count
        for warning in validation.warnings:
            print(f"WARNING: {warning}")
            logger.warning(warning)

        if options.method in {"random", "stratified"}:
            random_seed, generated = ensure_seed(options.seed)
            if generated:
                warning = f"No seed provided; generated seed {random_seed}."
                print(f"WARNING: {warning}")
                logger.warning(warning)

        if options.method == "random":
            sample = random_sample(validated, options.sample_size, random_seed)
            sample = add_sample_metadata(sample, options, random_seed, timestamp, None)
        elif options.method == "stratified":
            counts = validation.strata_counts
            if validation.strata_proportions:
                counts = largest_remainder_allocation(
                    options.sample_size, validation.strata_proportions
                )
            sampled, strata_rows = stratified_sample(
                validated,
                options.stratify_column,
                counts,
                random_seed,
                options.allow_shortfall,
            )
            sample = add_sample_metadata(
                sampled, options, random_seed, timestamp, options.stratify_column
            )

        _write_outputs(
            run_dir,
            options,
            source,
            validated,
            excluded_rows,
            duplicate_rows,
            sample,
            strata_rows,
            output_files,
        )
        logger.log("final status: success")
        print("Audit sampling run completed.")
    except AuditSamplingError as exc:
        duplicate_rows = exc.artifacts.get("duplicate_rows", duplicate_rows)
        logger.error(str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        _write_failure_outputs(
            run_dir,
            options,
            source,
            filtered,
            excluded_rows,
            duplicate_rows,
            output_files,
        )
        logger.log("final status: failed")
        raise
    finally:
        reconciliation = build_reconciliation(
            source_rows=len(source),
            blank_id_count=blank_id_count,
            duplicate_id_count=duplicate_id_count or len(duplicate_rows),
            excluded_rows=len(excluded_rows),
            validated_rows=len(validated),
            requested_sample_size=_requested_sample_size(options, strata_rows),
            final_sample_size=len(sample),
        )
        write_csv(reconciliation, run_dir / "population_reconciliation.csv")
        _track(output_files, "population_reconciliation.csv")
        methodology = build_methodology(
            input_file=input_path,
            input_sheet=options.sheet,
            input_sha256=input_hash,
            source_row_count=len(source),
            options=options,
            effective_id_column=effective_id_column,
            id_column_omitted=id_column_omitted,
            duplicate_id_count=duplicate_id_count or len(duplicate_rows),
            blank_id_count=blank_id_count,
            sample_size_actual=len(sample),
            random_seed=random_seed,
            strata_summary=strata_rows,
        )
        (run_dir / "methodology.txt").write_text(methodology)
        _track(output_files, "methodology.txt")
        manifest = build_manifest(
            run_timestamp_utc=timestamp,
            input_file=input_path,
            input_sha256=input_hash,
            input_sheet=options.sheet,
            options=options,
            effective_id_column=effective_id_column,
            id_column_omitted=id_column_omitted,
            sample_size_actual=len(sample),
            random_seed=random_seed,
            source_row_count=len(source),
            validated_population_count=len(validated),
            excluded_row_count=len(excluded_rows),
            duplicate_id_count=duplicate_id_count or len(duplicate_rows),
            blank_id_count=blank_id_count,
            output_files=sorted(output_files + ["run.log", "manifest.json"]),
        )
        write_manifest(manifest, run_dir / "manifest.json")
        logger.write(run_dir / "run.log")
    return run_dir


def add_sample_metadata(
    sample: pd.DataFrame,
    options,
    seed: int,
    timestamp: str,
    stratum_column: str | None,
) -> pd.DataFrame:
    source_columns = [column for column in sample.columns if column != "_audit_row_id"]
    output = sample[source_columns].copy()
    output.insert(0, "_selected_at_utc", timestamp)
    output.insert(0, "_random_seed", seed)
    output.insert(0, "_stratum", output[stratum_column] if stratum_column else "")
    output.insert(0, "_selection_method", options.method)
    output.insert(0, "_source_row_number", output.pop("_source_row_number"))
    output.insert(0, "_sample_id", range(1, len(output) + 1))
    return output


def _write_outputs(
    run_dir: Path,
    options,
    source: pd.DataFrame,
    validated: pd.DataFrame,
    excluded_rows: pd.DataFrame,
    duplicate_rows: pd.DataFrame,
    sample: pd.DataFrame,
    strata_rows: list[dict[str, object]],
    output_files: list[str],
) -> None:
    write_csv(validated, run_dir / "population_validated.csv")
    _track(output_files, "population_validated.csv")
    if options.method in {"random", "stratified"}:
        write_csv(sample, run_dir / "sample.csv")
        _track(output_files, "sample.csv")
    if not excluded_rows.empty:
        write_csv(excluded_rows, run_dir / "excluded_rows.csv")
        _track(output_files, "excluded_rows.csv")
    if not duplicate_rows.empty:
        write_csv(duplicate_rows, run_dir / "duplicate_ids.csv")
        _track(output_files, "duplicate_ids.csv")
    if options.method == "stratified":
        write_csv(build_strata_summary(strata_rows), run_dir / "strata_summary.csv")
        _track(output_files, "strata_summary.csv")


def _write_failure_outputs(
    run_dir: Path,
    options,
    source: pd.DataFrame,
    filtered: pd.DataFrame,
    excluded_rows: pd.DataFrame,
    duplicate_rows: pd.DataFrame,
    output_files: list[str],
) -> None:
    if not filtered.empty:
        write_csv(filtered, run_dir / "population_validated.csv")
        _track(output_files, "population_validated.csv")
    if not excluded_rows.empty:
        write_csv(excluded_rows, run_dir / "excluded_rows.csv")
        _track(output_files, "excluded_rows.csv")
    if not duplicate_rows.empty:
        write_csv(duplicate_rows, run_dir / "duplicate_ids.csv")
        _track(output_files, "duplicate_ids.csv")


def _concat_nonempty(frames: list[pd.DataFrame]) -> pd.DataFrame:
    nonempty = [frame for frame in frames if frame is not None and not frame.empty]
    if not nonempty:
        return pd.DataFrame()
    return pd.concat(nonempty, ignore_index=True)


def _track(output_files: list[str], filename: str) -> None:
    if filename not in output_files:
        output_files.append(filename)


def _requested_sample_size(options, strata_rows: list[dict[str, object]]) -> int | None:
    if options.sample_size is not None:
        return options.sample_size
    if strata_rows:
        return int(sum(row["Requested Sample Count"] for row in strata_rows))
    return None
