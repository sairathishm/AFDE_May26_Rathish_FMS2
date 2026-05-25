"""FastAPI application entry point — Phase 2."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from database import Base, engine
from etl.load import refresh_analytics
from database import SessionLocal
from routers import feedback as feedback_router
from routers import etl as etl_router
from routers import analytics as analytics_router
from seed import seed

# Create all tables — idempotent. Phase 2 adds etl_runs, program_summary, rating_summary.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Feedback Management System API",
    description=(
        "Phase 2 backend for the Feedback Management System. "
        "Phase 1 capabilities (full CRUD, search, filters, dashboard) plus a "
        "Pandas-based ETL pipeline that imports CSV/Excel feedback datasets, "
        "cleans them, refreshes analytics tables and exposes downloadable reports."
    ),
    version="2.0.0",
)

# CORS — allow the local Vite dev server and any localhost frontend to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feedback_router.router)
app.include_router(etl_router.router)
app.include_router(analytics_router.router)


@app.on_event("startup")
def on_startup() -> None:
    """Auto-seed the database on first launch and refresh analytics tables."""
    seed(force=False)
    # Make sure the analytics tables are populated even before any ETL run
    db = SessionLocal()
    try:
        refresh_analytics(db)
    finally:
        db.close()


@app.get("/", tags=["health"])
def root() -> dict:
    return {
        "service": "Feedback Management System",
        "status": "ok",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "healthy"}
