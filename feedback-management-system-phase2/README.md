# Feedback Management System — Phase 2

Phase 2 extends the Phase 1 Feedback Management System with a **Pandas-based ETL
pipeline** that imports CSV/Excel feedback datasets, cleans them, refreshes
analytics tables and exposes downloadable reports.

- **Frontend:** React 18 (Vite) + plain CSS
- **Backend:** FastAPI (Python 3.10 – 3.14 supported, tested on 3.14.5)
- **Database:** SQLite (via SQLAlchemy)
- **ETL:** Pandas + openpyxl

Phase 1 capabilities — full CRUD on feedback records, keyword search,
rating/program filters and the dashboard — are unchanged and still work.

---

## What's new in Phase 2

| Area     | Phase 2 addition |
|----------|------------------|
| Backend  | `etl/` package with extract → transform → load steps (Pandas) |
| Backend  | New tables: `etl_runs`, `program_summary`, `rating_summary` |
| Backend  | New routers: `/etl/*` and `/analytics/*` |
| Backend  | CSV downloads of cleaned data and per-program summary |
| Frontend | New **ETL Import** page (drag-and-drop CSV/Excel, run history) |
| Frontend | New **Analytics** dashboard (program/rating breakdowns, downloads) |
| Sample data | 128-row CSV (120 clean + 8 dirty) at `backend/sample_data/feedback_sample.csv` |

---

## Project structure

```
feedback-management-system-phase2/
├── README.md
├── backend/
│   ├── main.py               # FastAPI app + CORS + startup seed/refresh
│   ├── database.py           # SQLAlchemy engine & session (unchanged)
│   ├── models.py             # Phase 1 Feedback + Phase 2 EtlRun, ProgramSummary, RatingSummary
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── crud.py               # Data-access helpers (unchanged)
│   ├── seed.py               # Sample data loader for Phase 1 (unchanged)
│   ├── requirements.txt      # +pandas, +openpyxl, +numpy
│   ├── routers/
│   │   ├── feedback.py       # Phase 1 endpoints (unchanged)
│   │   ├── etl.py            # NEW — POST /etl/run, GET /etl/runs
│   │   └── analytics.py      # NEW — /analytics/overview, /programs, /ratings, downloads
│   ├── etl/                  # NEW — Pandas ETL package
│   │   ├── __init__.py
│   │   ├── extract.py        # CSV / Excel loader with column normalisation
│   │   ├── transform.py      # cleaning, validation, deduplication
│   │   ├── load.py           # writes to feedback + refreshes analytics tables
│   │   └── pipeline.py       # orchestrator with EtlRun audit row
│   └── sample_data/
│       ├── generate_sample.py
│       └── feedback_sample.csv   # 128 rows (120 clean + 8 dirty)
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx           # + /analytics and /etl routes
        ├── api.js            # + etlApi, analyticsApi
        ├── index.css         # + Phase 2 styles
        ├── components/
        │   ├── Navbar.jsx    # + Analytics & ETL Import links
        │   ├── SearchFilter.jsx
        │   └── StarRating.jsx
        └── pages/
            ├── Dashboard.jsx
            ├── FeedbackList.jsx
            ├── FeedbackDetails.jsx
            ├── SubmitFeedback.jsx
            ├── Analytics.jsx   # NEW
            └── EtlImport.jsx   # NEW
```

---

## Prerequisites

| Tool   | Version (tested)         |
|--------|--------------------------|
| Python | 3.10 – 3.14 (you have 3.14.5) |
| Node.js | 18+                      |
| npm    | 9+                       |

---

## Backend — setup & run

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies (now includes pandas + openpyxl)
pip install -r requirements.txt

# 3. Run the API
uvicorn main:app --reload --port 8000
```

The server starts at **http://localhost:8000**. On first launch:

1. SQLite tables are created (Phase 1 `feedback` + Phase 2 `etl_runs`, `program_summary`, `rating_summary`).
2. The 15 Phase 1 sample rows are seeded if `feedback` is empty.
3. Analytics tables are refreshed from `feedback`.

Useful URLs:

- **Swagger docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health:** http://localhost:8000/health

### Generating / using sample data

A 128-row CSV is already included at `backend/sample_data/feedback_sample.csv`.
To re-generate it (or also emit an `.xlsx` version):

```bash
cd backend/sample_data
python generate_sample.py            # writes feedback_sample.csv
python generate_sample.py --excel    # also writes feedback_sample.xlsx
```

The sample intentionally contains:

- ~120 clean records spread across 19 programs and 35 participants
- 2 duplicate rows
- 3 invalid ratings (0, 7, "abc")
- 2 rows with missing participant or program
- 1 row with whitespace/case-mangled fields

These let you see the ETL "Invalid" and "Duplicates" counters do something useful.

### Triggering ETL from the command line

The pipeline is a regular Python function — you don't have to go through HTTP:

```bash
cd backend
python -c "
from database import Base, engine, SessionLocal
import models
Base.metadata.create_all(bind=engine)
from etl import run_etl
db = SessionLocal()
result = run_etl(db, 'sample_data/feedback_sample.csv')
print(result.to_dict())
db.close()
"
```

---

## Frontend — setup & run

```bash
cd frontend
npm install
npm run dev
```

The app opens at **http://localhost:5173**. New nav items:

- **Analytics** — `/analytics`: live numbers from the analytics tables, with bar
  charts for rating distribution and a per-program summary table. Buttons let
  you download the cleaned dataset or per-program summary as CSV.
- **ETL Import** — `/etl`: drag-and-drop (or pick) a CSV/Excel file, run the
  ETL pipeline, and see a detailed result card plus history of recent runs.

The backend base URL is read from `VITE_API_BASE_URL` (defaults to
`http://localhost:8000`). Copy `.env.example` to `.env` to override.

---

## ETL pipeline — how it works

The pipeline lives in `backend/etl/` and runs **extract → transform → load**.

### 1. Extract (`extract.py`)

- Accepts CSV (`.csv`, `.tsv`, `.txt`) and Excel (`.xlsx`, `.xls`, `.xlsm`) files.
- Normalises column names (lower-case, spaces/dashes → underscores).
- Applies aliases so common header variations all map to canonical names:

  | Common header   | Mapped to          |
  |-----------------|--------------------|
  | name, participant, student_name | `participant_name` |
  | program, course, course_name, training | `program_name` |
  | score, stars    | `rating`          |
  | feedback, comment, remarks | `comments` |
  | date, submitted_at, submission_date | `submitted_date` |

### 2. Transform (`transform.py`)

- Verifies the required columns exist (`participant_name`, `program_name`, `rating`).
- Coerces `rating` to integer; drops rows that aren't a whole number in 1..5.
- Drops rows missing `participant_name` or `program_name` after stripping.
- Title-cases participant and program names; preserves short all-caps tokens (SQL, AWS).
- Collapses repeated whitespace inside text fields.
- Parses `submitted_date` (defaults to "now" when missing/unparseable).
- Removes exact duplicates on (participant, program, rating, comments, date).

Returns a `TransformResult` with input row count, invalid count, duplicate
count, output row count and a list of human-readable issues.

### 3. Load (`load.py`)

- Bulk-inserts the cleaned DataFrame into the `feedback` table.
- Recomputes the two analytics tables from the full `feedback` table:
  - `program_summary` — one row per program with totals, average, and
    positive (rating ≥ 4) / neutral (rating == 3) / negative (rating ≤ 2) counts.
  - `rating_summary` — one row per rating 1..5 with count and percent of total.

### 4. Orchestration (`pipeline.py`)

The `run_etl(db, file_path)` orchestrator:

- Writes an `EtlRun` audit row (`running`).
- Calls extract → transform → load.
- Updates the audit row with rows_extracted / rows_invalid / rows_duplicates / rows_loaded.
- Marks it `success` or `failed` (storing the error message).
- Returns an `ETLResult` dataclass with `to_dict()` for the API layer.

---

## API reference

Base URL: `http://localhost:8000`

### Phase 1 endpoints (unchanged)

| Method | Endpoint                  | Description                                       |
|--------|---------------------------|---------------------------------------------------|
| GET    | `/feedback`               | List all feedback (`rating`, `program`, `skip`, `limit`) |
| GET    | `/feedback/{id}`          | Retrieve one feedback record                      |
| GET    | `/feedback/stats`         | Aggregates: total, average rating, distribution   |
| POST   | `/feedback`               | Create a feedback record                          |
| PUT    | `/feedback/{id}`          | Update fields on an existing record               |
| DELETE | `/feedback/{id}`          | Delete a feedback record                          |
| GET    | `/search`                 | Keyword + rating + program search                 |
| GET    | `/health`                 | Liveness probe                                    |

### Phase 2 — ETL

| Method | Endpoint            | Description                                          |
|--------|---------------------|------------------------------------------------------|
| POST   | `/etl/run`          | Multipart upload (`file=…`); runs the ETL pipeline   |
| GET    | `/etl/runs`         | List the audit rows of recent ETL runs               |
| GET    | `/etl/runs/{id}`    | Get a single ETL run                                 |

`POST /etl/run` example:

```bash
curl -X POST http://localhost:8000/etl/run \
  -F "file=@backend/sample_data/feedback_sample.csv"
```

Response (success):

```json
{
  "run_id": 1,
  "source_file": "feedback_sample.csv",
  "status": "success",
  "rows_extracted": 128,
  "rows_invalid": 5,
  "rows_duplicates": 2,
  "rows_loaded": 121,
  "started_at": "2026-05-21T06:25:00.123456",
  "finished_at": "2026-05-21T06:25:00.987654",
  "issues": [
    "Dropped 5 rows with invalid rating or missing name/program",
    "Removed 2 duplicate rows"
  ],
  "error_message": null
}
```

### Phase 2 — Analytics

| Method | Endpoint                              | Description                                   |
|--------|---------------------------------------|-----------------------------------------------|
| GET    | `/analytics/overview`                 | Headline numbers for the analytics dashboard  |
| GET    | `/analytics/programs`                 | Per-program aggregates                        |
| GET    | `/analytics/ratings`                  | Per-rating bucket aggregates                  |
| POST   | `/analytics/refresh`                  | Recompute analytics tables from feedback      |
| GET    | `/analytics/download/cleaned.csv`     | Download the cleaned feedback dataset as CSV  |
| GET    | `/analytics/download/programs.csv`    | Download per-program summary as CSV           |

`GET /analytics/overview` example response:

```json
{
  "total_feedback": 136,
  "total_programs": 19,
  "average_rating": 3.65,
  "positive_pct": 58.82,
  "neutral_pct": 22.79,
  "negative_pct": 18.38,
  "top_program": "Generative AI Primer",
  "top_program_rating": 4.50,
  "bottom_program": "Cybersecurity Awareness",
  "bottom_program_rating": 1.50,
  "last_etl_run_at": "2026-05-21T06:25:00.123456"
}
```

---

## Database schema

### Phase 1 (unchanged)

Single table: `feedback`

| Column            | Type     | Notes                          |
|-------------------|----------|--------------------------------|
| feedback_id       | INTEGER  | Primary key, autoincrement     |
| participant_name  | TEXT     | Required, indexed              |
| program_name      | TEXT     | Required, indexed              |
| rating            | INTEGER  | Required, range 1–5            |
| comments          | TEXT     | Optional                       |
| submitted_at      | DATETIME | Defaults to `utcnow()`         |

### Phase 2 additions

`etl_runs`

| Column          | Type     | Notes                              |
|-----------------|----------|------------------------------------|
| run_id          | INTEGER  | PK, autoincrement                  |
| source_file     | TEXT     | Original filename of the upload    |
| started_at      | DATETIME | When the ETL job began             |
| finished_at     | DATETIME | When it ended (NULL if running)    |
| status          | TEXT     | `running` / `success` / `failed`   |
| rows_extracted  | INTEGER  | Rows read from the input           |
| rows_invalid    | INTEGER  | Rows dropped during transform      |
| rows_duplicates | INTEGER  | Duplicates removed                 |
| rows_loaded     | INTEGER  | Rows inserted into `feedback`      |
| error_message   | TEXT     | Populated when `status='failed'`   |

`program_summary`

| Column            | Type     | Notes                                       |
|-------------------|----------|---------------------------------------------|
| program_name      | TEXT     | Primary key                                 |
| total_feedback    | INTEGER  | Number of rows for this program             |
| average_rating    | REAL     | Mean rating, 2 decimal places               |
| positive_count    | INTEGER  | Rows with rating ≥ 4                        |
| neutral_count     | INTEGER  | Rows with rating == 3                       |
| negative_count    | INTEGER  | Rows with rating ≤ 2                        |
| last_refreshed_at | DATETIME | Timestamp of the last refresh               |

`rating_summary`

| Column            | Type     | Notes                                       |
|-------------------|----------|---------------------------------------------|
| rating            | INTEGER  | Primary key (1..5)                          |
| count             | INTEGER  | Rows with this rating                       |
| percent_of_total  | REAL     | Share of total feedback, 2 decimals         |
| last_refreshed_at | DATETIME | Timestamp of the last refresh               |

---

## Verified end-to-end on Python 3.14

The ETL pipeline was run against the provided sample dataset on Python 3.14.

```
Status: success
Extracted: 128
Invalid: 5         # 3 bad ratings + 2 missing name/program
Duplicates: 2
Loaded: 121
```

---

## Troubleshooting

- **`ModuleNotFoundError: pandas`** — install Phase 2 requirements: `pip install -r requirements.txt`.
- **`Unsupported file type '.json'`** — the ETL only accepts CSV/TSV/TXT/XLSX/XLS/XLSM.
- **Upload appears to succeed but no rows load** — check the `issues` list in the response. Typically the file is missing one of `participant_name`, `program_name`, or `rating`.
- **Analytics page shows zeros after manual edits via `/feedback`** — hit "Refresh analytics" (or `POST /analytics/refresh`); analytics tables are recomputed automatically only after ETL.
- **CORS errors in the browser console** — make sure the backend is on port 8000 (or extend `allow_origins` in `backend/main.py`).
