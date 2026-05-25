"""Phase 2 — Analytics REST endpoints.

GET  /analytics/overview              : Headline numbers for the analytics dashboard.
GET  /analytics/programs              : Per-program aggregates (table + chart data).
GET  /analytics/ratings               : Per-rating bucket aggregates.
POST /analytics/refresh               : Recompute analytics tables from feedback.
GET  /analytics/download/cleaned.csv  : Download the cleaned feedback dataset as CSV.
GET  /analytics/download/programs.csv : Download per-program summary as CSV.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from etl.load import refresh_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ------- helpers -------

def _stream_csv(rows: list[list], headers: list[str]) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
    )


# ------- endpoints -------

@router.get("/overview", response_model=schemas.AnalyticsOverviewOut)
def overview(db: Session = Depends(get_db)):
    """Headline analytics: totals, sentiment-ish split, top / bottom program."""
    total_feedback = db.query(func.count(models.Feedback.feedback_id)).scalar() or 0
    total_programs = db.query(func.count(func.distinct(models.Feedback.program_name))).scalar() or 0
    avg = db.query(func.avg(models.Feedback.rating)).scalar()
    avg_rating = round(float(avg), 2) if avg is not None else 0.0

    pos = db.query(func.count(models.Feedback.feedback_id)).filter(
        models.Feedback.rating >= 4
    ).scalar() or 0
    neut = db.query(func.count(models.Feedback.feedback_id)).filter(
        models.Feedback.rating == 3
    ).scalar() or 0
    neg = db.query(func.count(models.Feedback.feedback_id)).filter(
        models.Feedback.rating <= 2
    ).scalar() or 0

    pct = lambda n: round(100.0 * n / total_feedback, 2) if total_feedback else 0.0

    # Best & worst program by average rating (require >= 1 row)
    program_rows = (
        db.query(
            models.ProgramSummary.program_name,
            models.ProgramSummary.average_rating,
        )
        .filter(models.ProgramSummary.total_feedback > 0)
        .all()
    )

    top_program = bottom_program = None
    top_rating = bottom_rating = None
    if program_rows:
        ordered = sorted(program_rows, key=lambda r: (r.average_rating, r.program_name))
        bottom_program = ordered[0].program_name
        bottom_rating = round(float(ordered[0].average_rating), 2)
        top_program = ordered[-1].program_name
        top_rating = round(float(ordered[-1].average_rating), 2)

    last_run = (
        db.query(models.EtlRun)
        .order_by(models.EtlRun.started_at.desc())
        .first()
    )

    return schemas.AnalyticsOverviewOut(
        total_feedback=int(total_feedback),
        total_programs=int(total_programs),
        average_rating=avg_rating,
        positive_pct=pct(pos),
        neutral_pct=pct(neut),
        negative_pct=pct(neg),
        top_program=top_program,
        top_program_rating=top_rating,
        bottom_program=bottom_program,
        bottom_program_rating=bottom_rating,
        last_etl_run_at=last_run.started_at if last_run else None,
    )


@router.get("/programs", response_model=List[schemas.ProgramSummaryOut])
def per_program(db: Session = Depends(get_db)):
    return (
        db.query(models.ProgramSummary)
        .order_by(models.ProgramSummary.average_rating.desc())
        .all()
    )


@router.get("/ratings", response_model=List[schemas.RatingSummaryOut])
def per_rating(db: Session = Depends(get_db)):
    return (
        db.query(models.RatingSummary)
        .order_by(models.RatingSummary.rating.asc())
        .all()
    )


@router.post("/refresh")
def refresh(db: Session = Depends(get_db)):
    """Recompute analytics tables from the current feedback table.

    Useful when feedback has been modified via the regular CRUD endpoints
    (without going through ETL).
    """
    result = refresh_analytics(db)
    return {"status": "ok", **result, "refreshed_at": datetime.utcnow().isoformat()}


@router.get("/download/cleaned.csv")
def download_cleaned(db: Session = Depends(get_db)):
    """Download the full cleaned feedback table as a CSV file."""
    rows = (
        db.query(models.Feedback)
        .order_by(models.Feedback.submitted_at.desc())
        .all()
    )
    data = [
        [
            r.feedback_id,
            r.participant_name,
            r.program_name,
            r.rating,
            (r.comments or "").replace("\n", " ").replace("\r", " "),
            r.submitted_at.isoformat() if r.submitted_at else "",
        ]
        for r in rows
    ]
    headers = ["feedback_id", "participant_name", "program_name", "rating", "comments", "submitted_at"]
    resp = _stream_csv(data, headers)
    resp.headers["Content-Disposition"] = 'attachment; filename="feedback_cleaned.csv"'
    return resp


@router.get("/download/programs.csv")
def download_programs(db: Session = Depends(get_db)):
    """Download per-program analytics summary as CSV."""
    rows = (
        db.query(models.ProgramSummary)
        .order_by(models.ProgramSummary.average_rating.desc())
        .all()
    )
    data = [
        [
            r.program_name,
            r.total_feedback,
            r.average_rating,
            r.positive_count,
            r.neutral_count,
            r.negative_count,
            r.last_refreshed_at.isoformat() if r.last_refreshed_at else "",
        ]
        for r in rows
    ]
    headers = [
        "program_name", "total_feedback", "average_rating",
        "positive_count", "neutral_count", "negative_count", "last_refreshed_at",
    ]
    resp = _stream_csv(data, headers)
    resp.headers["Content-Disposition"] = 'attachment; filename="program_summary.csv"'
    return resp
