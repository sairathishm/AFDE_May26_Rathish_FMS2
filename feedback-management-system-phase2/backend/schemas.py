"""Pydantic schemas used to validate API payloads and shape responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ===== Phase 1 — Feedback =====

class FeedbackBase(BaseModel):
    participant_name: str = Field(..., min_length=1, max_length=150)
    program_name: str = Field(..., min_length=1, max_length=200)
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 (Poor) to 5 (Excellent)")
    comments: Optional[str] = Field("", max_length=2000)


class FeedbackCreate(FeedbackBase):
    """Payload accepted by POST /feedback."""


class FeedbackUpdate(BaseModel):
    """Payload accepted by PUT /feedback/{id}. All fields optional."""

    participant_name: Optional[str] = Field(None, min_length=1, max_length=150)
    program_name: Optional[str] = Field(None, min_length=1, max_length=200)
    rating: Optional[int] = Field(None, ge=1, le=5)
    comments: Optional[str] = Field(None, max_length=2000)


class FeedbackOut(FeedbackBase):
    """Shape returned by all read endpoints."""

    feedback_id: int
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    """Aggregate stats used by the dashboard."""

    total_feedback: int
    average_rating: float
    rating_distribution: dict[int, int]


# ===== Phase 2 — Analytics & ETL =====

class EtlRunOut(BaseModel):
    """Audit record for one ETL execution."""

    run_id: int
    source_file: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    rows_extracted: int
    rows_invalid: int
    rows_duplicates: int
    rows_loaded: int
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProgramSummaryOut(BaseModel):
    program_name: str
    total_feedback: int
    average_rating: float
    positive_count: int
    neutral_count: int
    negative_count: int
    last_refreshed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatingSummaryOut(BaseModel):
    rating: int
    count: int
    percent_of_total: float
    last_refreshed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyticsOverviewOut(BaseModel):
    """Headline analytics for the Phase 2 dashboard."""

    total_feedback: int
    total_programs: int
    average_rating: float
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    top_program: Optional[str] = None
    top_program_rating: Optional[float] = None
    bottom_program: Optional[str] = None
    bottom_program_rating: Optional[float] = None
    last_etl_run_at: Optional[datetime] = None
