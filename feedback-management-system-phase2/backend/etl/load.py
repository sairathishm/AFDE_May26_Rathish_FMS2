"""Phase 2 ETL — LOAD step.

Two responsibilities:
    1. Insert cleaned rows into the `feedback` table (Phase 1 raw store).
    2. Refresh the analytics tables (`program_summary`, `rating_summary`) from
       the full feedback table so they always reflect the latest state.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def load_feedback_rows(db: Session, df: pd.DataFrame) -> int:
    """Insert the cleaned DataFrame into the feedback table.

    Returns the number of rows actually inserted.
    """
    if df.empty:
        return 0

    rows = [
        models.Feedback(
            participant_name=row.participant_name,
            program_name=row.program_name,
            rating=int(row.rating),
            comments=row.comments or "",
            submitted_at=row.submitted_date.to_pydatetime()
                if hasattr(row.submitted_date, "to_pydatetime")
                else row.submitted_date,
        )
        for row in df.itertuples(index=False)
    ]
    db.add_all(rows)
    db.commit()
    return len(rows)


def refresh_analytics(db: Session) -> dict:
    """Rebuild program_summary and rating_summary from the feedback table."""
    now = datetime.utcnow()

    # ---- Program summary ----
    db.query(models.ProgramSummary).delete()
    program_rows = (
        db.query(
            models.Feedback.program_name,
            func.count(models.Feedback.feedback_id).label("total"),
            func.avg(models.Feedback.rating).label("avg_rating"),
            func.sum(
                # SQLite has no boolean->int cast issue when using CASE
                func.coalesce(
                    func.nullif(
                        # 1 when rating >= 4 else 0
                        (models.Feedback.rating >= 4),
                        False,
                    ),
                    False,
                )
            ),
        )
        .group_by(models.Feedback.program_name)
        .all()
    )

    # We use a manual loop to compute pos/neut/neg counts portably
    summary_objs = []
    for program_name, total, avg_rating, _maybe_pos in program_rows:
        pos = db.query(func.count(models.Feedback.feedback_id)).filter(
            models.Feedback.program_name == program_name,
            models.Feedback.rating >= 4,
        ).scalar() or 0
        neut = db.query(func.count(models.Feedback.feedback_id)).filter(
            models.Feedback.program_name == program_name,
            models.Feedback.rating == 3,
        ).scalar() or 0
        neg = db.query(func.count(models.Feedback.feedback_id)).filter(
            models.Feedback.program_name == program_name,
            models.Feedback.rating <= 2,
        ).scalar() or 0
        summary_objs.append(
            models.ProgramSummary(
                program_name=program_name,
                total_feedback=int(total or 0),
                average_rating=round(float(avg_rating or 0.0), 2),
                positive_count=int(pos),
                neutral_count=int(neut),
                negative_count=int(neg),
                last_refreshed_at=now,
            )
        )
    db.add_all(summary_objs)

    # ---- Rating summary ----
    db.query(models.RatingSummary).delete()
    total_feedback = db.query(func.count(models.Feedback.feedback_id)).scalar() or 0
    rating_counts = dict(
        db.query(models.Feedback.rating, func.count(models.Feedback.feedback_id))
        .group_by(models.Feedback.rating)
        .all()
    )
    rating_objs = []
    for r in range(1, 6):
        count = int(rating_counts.get(r, 0))
        pct = round(100.0 * count / total_feedback, 2) if total_feedback else 0.0
        rating_objs.append(
            models.RatingSummary(
                rating=r,
                count=count,
                percent_of_total=pct,
                last_refreshed_at=now,
            )
        )
    db.add_all(rating_objs)
    db.commit()

    return {
        "programs": len(summary_objs),
        "ratings": len(rating_objs),
        "total_feedback": int(total_feedback),
    }
