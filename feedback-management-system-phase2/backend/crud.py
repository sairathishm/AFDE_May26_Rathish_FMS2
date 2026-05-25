"""CRUD helpers — pure data access, no HTTP awareness."""
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
import schemas


def create_feedback(db: Session, payload: schemas.FeedbackCreate) -> models.Feedback:
    feedback = models.Feedback(
        participant_name=payload.participant_name.strip(),
        program_name=payload.program_name.strip(),
        rating=payload.rating,
        comments=(payload.comments or "").strip(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback(db: Session, feedback_id: int) -> Optional[models.Feedback]:
    return db.query(models.Feedback).filter(models.Feedback.feedback_id == feedback_id).first()


def list_feedback(
    db: Session,
    rating: Optional[int] = None,
    program: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Feedback]:
    query = db.query(models.Feedback)
    if rating is not None:
        query = query.filter(models.Feedback.rating == rating)
    if program:
        query = query.filter(models.Feedback.program_name.ilike(f"%{program}%"))
    return (
        query.order_by(models.Feedback.submitted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def search_feedback(
    db: Session,
    keyword: Optional[str] = None,
    rating: Optional[int] = None,
    program: Optional[str] = None,
) -> list[models.Feedback]:
    query = db.query(models.Feedback)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                models.Feedback.participant_name.ilike(like),
                models.Feedback.program_name.ilike(like),
                models.Feedback.comments.ilike(like),
            )
        )
    if rating is not None:
        query = query.filter(models.Feedback.rating == rating)
    if program:
        query = query.filter(models.Feedback.program_name.ilike(f"%{program}%"))
    return query.order_by(models.Feedback.submitted_at.desc()).all()


def update_feedback(
    db: Session, feedback_id: int, payload: schemas.FeedbackUpdate
) -> Optional[models.Feedback]:
    feedback = get_feedback(db, feedback_id)
    if not feedback:
        return None
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(feedback, field, value)
    db.commit()
    db.refresh(feedback)
    return feedback


def delete_feedback(db: Session, feedback_id: int) -> bool:
    feedback = get_feedback(db, feedback_id)
    if not feedback:
        return False
    db.delete(feedback)
    db.commit()
    return True


def get_stats(db: Session) -> dict:
    total = db.query(func.count(models.Feedback.feedback_id)).scalar() or 0
    avg = db.query(func.avg(models.Feedback.rating)).scalar()
    avg_rating = round(float(avg), 2) if avg is not None else 0.0

    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    rows = (
        db.query(models.Feedback.rating, func.count(models.Feedback.feedback_id))
        .group_by(models.Feedback.rating)
        .all()
    )
    for rating, count in rows:
        distribution[int(rating)] = int(count)

    return {
        "total_feedback": int(total),
        "average_rating": avg_rating,
        "rating_distribution": distribution,
    }
