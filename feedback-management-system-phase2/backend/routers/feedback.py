"""Feedback REST endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db

router = APIRouter(tags=["feedback"])


@router.get("/feedback", response_model=list[schemas.FeedbackOut])
def list_feedback(
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by exact rating"),
    program: Optional[str] = Query(None, description="Filter by program name (partial match)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve all feedback (optionally filtered, paginated)."""
    return crud.list_feedback(db, rating=rating, program=program, skip=skip, limit=limit)


@router.get("/search", response_model=list[schemas.FeedbackOut])
def search(
    keyword: Optional[str] = Query(None, description="Search across name, program, comments"),
    rating: Optional[int] = Query(None, ge=1, le=5),
    program: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Keyword + filter search."""
    return crud.search_feedback(db, keyword=keyword, rating=rating, program=program)


@router.get("/feedback/stats", response_model=schemas.StatsOut)
def stats(db: Session = Depends(get_db)):
    """Dashboard aggregates: count, average, rating distribution."""
    return crud.get_stats(db)


@router.get("/feedback/{feedback_id}", response_model=schemas.FeedbackOut)
def get_one(feedback_id: int, db: Session = Depends(get_db)):
    """Retrieve a single feedback record by id."""
    feedback = crud.get_feedback(db, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")
    return feedback


@router.post(
    "/feedback",
    response_model=schemas.FeedbackOut,
    status_code=status.HTTP_201_CREATED,
)
def create(payload: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    """Submit new feedback."""
    return crud.create_feedback(db, payload)


@router.put("/feedback/{feedback_id}", response_model=schemas.FeedbackOut)
def update(
    feedback_id: int,
    payload: schemas.FeedbackUpdate,
    db: Session = Depends(get_db),
):
    """Update feedback (admin)."""
    updated = crud.update_feedback(db, feedback_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")
    return updated


@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_200_OK)
def delete(feedback_id: int, db: Session = Depends(get_db)):
    """Delete feedback."""
    deleted = crud.delete_feedback(db, feedback_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")
    return {"detail": f"Feedback {feedback_id} deleted"}
