"""Phase 2 ETL — EXTRACT step.

Reads a CSV or Excel file into a pandas DataFrame. Column names are normalised
(lower-cased, spaces / dashes converted to underscores) so the downstream
TRANSFORM step does not need to deal with naming variations.

Expected columns (after normalisation):
    participant_name, program_name, rating, comments, submitted_date
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

CSV_EXTS = {".csv", ".tsv", ".txt"}
EXCEL_EXTS = {".xlsx", ".xls", ".xlsm"}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=lambda c: (
        str(c).strip().lower()
              .replace("-", "_")
              .replace(" ", "_")
    ))
    # Common header variations -> canonical names
    aliases = {
        "name": "participant_name",
        "participant": "participant_name",
        "student_name": "participant_name",
        "program": "program_name",
        "course": "program_name",
        "course_name": "program_name",
        "training": "program_name",
        "score": "rating",
        "stars": "rating",
        "feedback": "comments",
        "comment": "comments",
        "remarks": "comments",
        "date": "submitted_date",
        "submitted_at": "submitted_date",
        "submission_date": "submitted_date",
    }
    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})
    return df


def extract(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV/TSV/Excel file into a DataFrame with normalised columns.

    Raises:
        FileNotFoundError: if the path does not exist.
        ValueError: if the file extension is unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    ext = path.suffix.lower()
    if ext in CSV_EXTS:
        sep = "\t" if ext == ".tsv" else ","
        df = pd.read_csv(path, sep=sep, encoding="utf-8-sig", keep_default_na=True)
    elif ext in EXCEL_EXTS:
        df = pd.read_excel(path, engine="openpyxl")
    else:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Supported: {sorted(CSV_EXTS | EXCEL_EXTS)}"
        )

    df = _normalise_columns(df)
    return df
