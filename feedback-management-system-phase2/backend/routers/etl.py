"""Phase 2 — ETL REST endpoints.

POST /etl/run            : Trigger an ETL run against an uploaded CSV/Excel file.
GET  /etl/runs           : List all ETL runs (audit trail), most recent first.
GET  /etl/runs/{id}      : Get one ETL run.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from etl import run_etl

router = APIRouter(prefix="/etl", tags=["etl"])

# Where uploaded files are kept for the duration of the request
UPLOAD_DIR = Path(tempfile.gettempdir()) / "feedback_etl_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTS = {".csv", ".tsv", ".txt", ".xlsx", ".xls", ".xlsm"}


@router.post("/run", status_code=status.HTTP_200_OK)
async def trigger_etl(
    file: UploadFile = File(..., description="CSV or Excel file with feedback data"),
    db: Session = Depends(get_db),
):
    """Upload a CSV/Excel file and run the ETL pipeline against it."""
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTS)}",
        )

    # Persist upload to a temp file so the ETL extractor can open it
    dest = UPLOAD_DIR / filename
    try:
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
    finally:
        await file.close()

    result = run_etl(db, dest)

    # Best-effort cleanup; ignore if it fails (Windows file locks etc.)
    try:
        dest.unlink(missing_ok=True)
    except Exception:
        pass

    if result.status == "failed":
        # 422 keeps the audit row but signals to the client that nothing loaded
        raise HTTPException(status_code=422, detail=result.to_dict())

    return result.to_dict()


@router.get("/runs", response_model=List[schemas.EtlRunOut])
def list_runs(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(models.EtlRun)
        .order_by(models.EtlRun.started_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/runs/{run_id}", response_model=schemas.EtlRunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(models.EtlRun).filter(models.EtlRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"ETL run {run_id} not found")
    return run
