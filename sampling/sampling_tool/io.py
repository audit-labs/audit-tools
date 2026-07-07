"""Input and output helpers for audit sampling."""

from __future__ import annotations

from pathlib import Path
import hashlib

import pandas as pd


SUPPORTED_EXCEL_SUFFIXES = {".xlsx", ".xls", ".xlsm"}


class AuditSamplingError(Exception):
    """Raised when the sampling request cannot be completed."""

    def __init__(self, message: str, **artifacts) -> None:
        super().__init__(message)
        self.artifacts = artifacts


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_population(input_path: Path, sheet: str | None = None) -> pd.DataFrame:
    if not input_path.exists():
        raise AuditSamplingError(f"Input file does not exist: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(input_path)
    elif suffix in SUPPORTED_EXCEL_SUFFIXES:
        excel = pd.ExcelFile(input_path)
        if sheet is None:
            if len(excel.sheet_names) != 1:
                names = ", ".join(excel.sheet_names)
                raise AuditSamplingError(
                    "Excel workbook has multiple sheets. Provide --sheet. "
                    f"Available sheets: {names}"
                )
            sheet = excel.sheet_names[0]
        frame = pd.read_excel(input_path, sheet_name=sheet)
    else:
        supported = ".csv, .xlsx, .xls, .xlsm"
        raise AuditSamplingError(
            f"Unsupported input extension '{suffix}'. Supported: {supported}"
        )

    frame = frame.copy()
    frame.insert(0, "_source_row_number", range(2, len(frame) + 2))
    return frame


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False)
