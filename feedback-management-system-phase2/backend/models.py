"""SQLAlchemy ORM models.

Phase 1 model (Feedback) kept untouched. Phase 2 adds three analytics tables:
- EtlRun         : one row per ETL execution (audit trail)
- ProgramSummary : per-program aggregates refreshed by ETL
- RatingSummary  : per-rating aggregates refreshed by ETL
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from database import Base


class Feedback(Base):
    """Feedback record submitted by a participant. (Phase 1)"""

    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    participant_name = Column(String(150), nullable=False, index=True)
    program_name = Column(String(200), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1..5
    comments = Column(Text, nullable=True, default="")
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ===== Phase 2 — Analytics tables =====

class EtlRun(Base):
    """Audit row for every ETL job that has executed."""

    __tablename__ = "etl_runs"

    run_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_file = Column(String(255), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running | success | failed

    rows_extracted = Column(Integer, nullable=False, default=0)
    rows_invalid = Column(Integer, nullable=False, default=0)      # dropped during transform
    rows_duplicates = Column(Integer, nullable=False, default=0)   # removed as duplicates
    rows_loaded = Column(Integer, nullable=False, default=0)       # inserted into feedback table

    error_message = Column(Text, nullable=True)


class ProgramSummary(Base):
    """Per-program aggregate refreshed at the end of each ETL run."""

    __tablename__ = "program_summary"

    program_name = Column(String(200), primary_key=True)
    total_feedback = Column(Integer, nullable=False, default=0)
    average_rating = Column(Float, nullable=False, default=0.0)
    positive_count = Column(Integer, nullable=False, default=0)   # rating >= 4
    neutral_count = Column(Integer, nullable=False, default=0)    # rating == 3
    negative_count = Column(Integer, nullable=False, default=0)   # rating <= 2
    last_refreshed_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class RatingSummary(Base):
    """One row per rating bucket (1..5), refreshed by ETL."""

    __tablename__ = "rating_summary"

    rating = Column(Integer, primary_key=True)  # 1..5
    count = Column(Integer, nullable=False, default=0)
    percent_of_total = Column(Float, nullable=False, default=0.0)
    last_refreshed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
