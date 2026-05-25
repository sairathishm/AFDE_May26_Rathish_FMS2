"""Generate a sample feedback dataset (>= 100 records) for the ETL pipeline.

The generated CSV intentionally contains some dirty rows — invalid ratings,
duplicates, extra whitespace, missing fields — so the ETL pipeline has
something to clean up.

Run with:
    python generate_sample.py             # writes feedback_sample.csv
    python generate_sample.py --excel     # also writes feedback_sample.xlsx
"""
from __future__ import annotations

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent

NAMES = [
    "Aarav Sharma", "Priya Iyer", "Liam O'Connor", "Mei Lin", "Sai Rathish",
    "Ananya Gupta", "Rohan Mehta", "Sara Ahmed", "Diego Alvarez", "Hannah Kim",
    "Vivek Nair", "Emily Carter", "Karthik Subramanian", "Olivia Brown", "Noah Singh",
    "Ishaan Patel", "Layla Hassan", "Daniel Wright", "Sophia Martinez", "Arjun Reddy",
    "Yuki Tanaka", "Marco Rossi", "Fatima Khan", "Ethan Wilson", "Riya Joshi",
    "Maya Verma", "Lucas Bennett", "Zara Shaikh", "Hiro Sato", "Anna Schmidt",
    "Oluwaseun Adebayo", "Camille Dubois", "Henry Nguyen", "Aisha Bello", "Tariq Malik",
]

PROGRAMS = [
    "Python Fundamentals Bootcamp", "React Crash Course", "Data Engineering with Spark",
    "FastAPI Workshop", "Cloud Foundations on AWS", "SQL for Analytics",
    "Docker & Kubernetes 101", "Generative AI Primer", "MLOps Foundations",
    "Agile Project Management", "Power BI for Business Users", "Cybersecurity Awareness",
    "TypeScript Deep Dive", "Communication Skills Workshop", "DevOps Fundamentals",
    "Microservices Architecture", "Machine Learning with scikit-learn",
    "Data Visualization with Tableau", "Leadership Essentials",
]

COMMENTS_BY_RATING = {
    5: [
        "Excellent trainer, very engaging.",
        "Best session I attended this year.",
        "Crystal clear explanations.",
        "Loved the hands-on labs.",
        "Highly recommended for everyone.",
    ],
    4: [
        "Good content, well paced.",
        "Useful workshop, learned a lot.",
        "Solid material, minor improvements possible.",
        "Practical examples were helpful.",
        "Trainer was knowledgeable.",
    ],
    3: [
        "Decent overview, needs more depth.",
        "OK pace, could be more interactive.",
        "Average — slides were a bit dense.",
        "Helpful but felt rushed near the end.",
        "Reasonable, would benefit from exercises.",
    ],
    2: [
        "Too basic for experienced participants.",
        "Material felt outdated.",
        "Trainer struggled with questions.",
        "Slides had typos and were hard to read.",
        "Not engaging, lost attention.",
    ],
    1: [
        "Poor session, did not meet expectations.",
        "Felt like a checkbox course.",
        "Wasted time, no real learning.",
        "Trainer was unprepared.",
        "Very disappointing.",
    ],
}


def build_clean_rows(n: int) -> list[dict]:
    rnd = random.Random(20260521)
    start = datetime(2026, 1, 1)
    rows = []
    for i in range(n):
        rating = rnd.choices([5, 4, 3, 2, 1], weights=[0.30, 0.30, 0.20, 0.12, 0.08])[0]
        rows.append({
            "participant_name": rnd.choice(NAMES),
            "program_name": rnd.choice(PROGRAMS),
            "rating": rating,
            "comments": rnd.choice(COMMENTS_BY_RATING[rating]),
            "submitted_date": (start + timedelta(days=rnd.randint(0, 130),
                                                 hours=rnd.randint(0, 23))).isoformat(),
        })
    return rows


def add_dirty_rows(rows: list[dict]) -> list[dict]:
    """Sprinkle in dirty data so the ETL pipeline has something to clean up."""
    dirty = []

    # 1. Duplicate of an existing row
    if rows:
        dirty.append(dict(rows[0]))
        dirty.append(dict(rows[1]))

    # 2. Invalid ratings (0, 7, "abc")
    dirty.append({
        "participant_name": "  Test  user  ",
        "program_name": "SQL for Analytics",
        "rating": 0,
        "comments": "rating too low",
        "submitted_date": "2026-03-15",
    })
    dirty.append({
        "participant_name": "Another User",
        "program_name": "FastAPI Workshop",
        "rating": 7,
        "comments": "rating too high",
        "submitted_date": "2026-03-16",
    })
    dirty.append({
        "participant_name": "Bad Rating",
        "program_name": "Cloud Foundations on AWS",
        "rating": "abc",
        "comments": "rating not a number",
        "submitted_date": "2026-03-17",
    })

    # 3. Missing participant_name or program_name
    dirty.append({
        "participant_name": "",
        "program_name": "DevOps Fundamentals",
        "rating": 4,
        "comments": "missing name",
        "submitted_date": "2026-03-18",
    })
    dirty.append({
        "participant_name": "Missing Program",
        "program_name": "",
        "rating": 3,
        "comments": "missing program",
        "submitted_date": "2026-03-19",
    })

    # 4. Whitespace / casing variations
    dirty.append({
        "participant_name": "   priya   IYER   ",
        "program_name": "  react crash course  ",
        "rating": 5,
        "comments": "lots   of    whitespace",
        "submitted_date": "2026-04-01",
    })

    return rows + dirty


def write_csv(rows: list[dict], path: Path) -> None:
    fields = ["participant_name", "program_name", "rating", "comments", "submitted_date"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fields})
    print(f"Wrote {len(rows)} rows -> {path}")


def write_excel(rows: list[dict], path: Path) -> None:
    try:
        from openpyxl import Workbook
    except ImportError:
        print("openpyxl not installed — skipping .xlsx output (pip install openpyxl)")
        return
    fields = ["participant_name", "program_name", "rating", "comments", "submitted_date"]
    wb = Workbook()
    ws = wb.active
    ws.title = "feedback"
    ws.append(fields)
    for r in rows:
        ws.append([r.get(k, "") for k in fields])
    wb.save(path)
    print(f"Wrote {len(rows)} rows -> {path}")


def main() -> None:
    clean = build_clean_rows(120)            # well above the 100-row minimum
    all_rows = add_dirty_rows(clean)
    write_csv(all_rows, OUT_DIR / "feedback_sample.csv")
    if "--excel" in sys.argv:
        write_excel(all_rows, OUT_DIR / "feedback_sample.xlsx")
    print(f"Total rows (clean + dirty): {len(all_rows)}")


if __name__ == "__main__":
    main()
