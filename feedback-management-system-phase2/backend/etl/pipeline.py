"""Phase 2 ETL — orchestrator.

Glue that wires extract → transform → load together, while writing an
`EtlRun` audit row tracking every execution.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

import models
from .extract import extract
from .transform import transform
from .load import load_feedback_rows, refresh_analytics


@dataclass
class ETLResult:
    run_id: int
    source_file: str
    status: str
    rows_extracted: int
    rows_invalid: int
    rows_duplicates: int
    rows_loaded: int
    started_at: datetime
    finished_at: Optional[datetime]
    issues: List[str]
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["started_at"] = self.started_at.isoformat()
        d["finished_at"] = self.finished_at.isoformat() if self.finished_at else None
        return d


def run_etl(db: Session, file_path: str | Path) -> ETLResult:
    """Run the full ETL pipeline against the given file.

    Always writes an EtlRun audit row, even on failure.
    """
    file_path = Path(file_path)
    run = models.EtlRun(
        source_file=file_path.name,
        started_at=datetime.utcnow(),
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    issues: List[str] = []
    try:
        # EXTRACT
        df = extract(file_path)
        rows_extracted = len(df)

        # TRANSFORM
        result = transform(df)
        issues.extend(result.issues)

        # LOAD
        rows_loaded = load_feedback_rows(db, result.df)

        # Refresh analytics tables from the (now updated) feedback table
        refresh_analytics(db)

        run.rows_extracted = rows_extracted
        run.rows_invalid = result.rows_invalid
        run.rows_duplicates = result.rows_duplicates
        run.rows_loaded = rows_loaded
        run.status = "success"
        run.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(run)

        return ETLResult(
            run_id=run.run_id,
            source_file=run.source_file,
            status=run.status,
            rows_extracted=run.rows_extracted,
            rows_invalid=run.rows_invalid,
            rows_duplicates=run.rows_duplicates,
            rows_loaded=run.rows_loaded,
            started_at=run.started_at,
            finished_at=run.finished_at,
            issues=issues,
        )

    except Exception as exc:  # noqa: BLE001
        run.status = "failed"
        run.finished_at = datetime.utcnow()
        run.error_message = f"{type(exc).__name__}: {exc}"
        db.commit()
        db.refresh(run)
        return ETLResult(
            run_id=run.run_id,
            source_file=run.source_file,
            status=run.status,
            rows_extracted=run.rows_extracted,
            rows_invalid=run.rows_invalid,
            rows_duplicates=run.rows_duplicates,
            rows_loaded=run.rows_loaded,
            started_at=run.started_at,
            finished_at=run.finished_at,
            issues=issues,
            error_message=run.error_message,
        )
