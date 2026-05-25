"""Phase 2 ETL — TRANSFORM step.

Responsibilities:
    1. Verify the required columns exist; create empty ones if optional fields are missing.
    2. Coerce types (rating -> int, submitted_date -> datetime).
    3. Drop rows with invalid ratings (must be 1..5 after coercion).
    4. Drop rows missing mandatory text fields (participant_name, program_name).
    5. Standardise text (strip whitespace, collapse repeated spaces, title-case names).
    6. Remove duplicate rows (same participant + program + rating + comments + date).

Returns a `TransformResult` describing what was kept / removed so the ETL run
audit row can record those counts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List

import pandas as pd

REQUIRED_COLUMNS = ["participant_name", "program_name", "rating"]
OPTIONAL_COLUMNS = ["comments", "submitted_date"]
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

_WHITESPACE = re.compile(r"\s+")


@dataclass
class TransformResult:
    df: pd.DataFrame
    rows_in: int
    rows_invalid: int
    rows_duplicates: int
    rows_out: int
    issues: List[str]


def _clean_text(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    text = _WHITESPACE.sub(" ", text)
    return text


def _title_case_name(value) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    # Title-case but preserve all-caps acronyms (e.g. SQL, AWS)
    return " ".join(part if part.isupper() and len(part) <= 4 else part.capitalize()
                    for part in text.split())


def transform(df: pd.DataFrame) -> TransformResult:
    issues: List[str] = []
    rows_in = len(df)

    # 1. Ensure required + optional columns exist
    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        raise ValueError(
            f"Input is missing required columns: {missing_required}. "
            f"Expected at least: {REQUIRED_COLUMNS}"
        )
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = None
            issues.append(f"Column '{col}' missing — defaulted to NULL")

    df = df[ALL_COLUMNS].copy()

    # 2. Coerce rating to int, drop invalid (NaN, non-numeric, out of 1..5)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    invalid_rating_mask = (
        df["rating"].isna()
        | (df["rating"] < 1)
        | (df["rating"] > 5)
        | (df["rating"] != df["rating"].round(0))  # non-integer values
    )
    rows_invalid_rating = int(invalid_rating_mask.sum())

    # 3. Drop rows with missing participant_name / program_name
    df["participant_name"] = df["participant_name"].map(_title_case_name)
    df["program_name"] = df["program_name"].map(_title_case_name)
    invalid_text_mask = (
        (df["participant_name"] == "") | (df["program_name"] == "")
    )
    # Combine invalidity reasons (a row may be invalid for multiple reasons)
    invalid_mask = invalid_rating_mask | invalid_text_mask
    rows_invalid = int(invalid_mask.sum())

    df = df.loc[~invalid_mask].copy()
    df["rating"] = df["rating"].astype(int)

    # 4. Standardise comments and date
    df["comments"] = df["comments"].map(_clean_text)
    df["submitted_date"] = pd.to_datetime(df["submitted_date"], errors="coerce")
    # Fill missing dates with "now" so loaded rows always have a timestamp
    now = pd.Timestamp(datetime.utcnow())
    df["submitted_date"] = df["submitted_date"].fillna(now)

    # 5. Drop exact duplicates on (participant, program, rating, comments, date)
    dedup_subset = ["participant_name", "program_name", "rating", "comments", "submitted_date"]
    before_dedup = len(df)
    df = df.drop_duplicates(subset=dedup_subset, keep="first").reset_index(drop=True)
    rows_duplicates = before_dedup - len(df)

    if rows_invalid:
        issues.append(f"Dropped {rows_invalid} rows with invalid rating or missing name/program")
    if rows_duplicates:
        issues.append(f"Removed {rows_duplicates} duplicate rows")

    return TransformResult(
        df=df,
        rows_in=rows_in,
        rows_invalid=rows_invalid,
        rows_duplicates=rows_duplicates,
        rows_out=len(df),
        issues=issues,
    )
    )
