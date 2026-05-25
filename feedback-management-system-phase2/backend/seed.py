"""Seed the database with sample feedback so the dashboard has data on first run.

Run manually with:  python seed.py
The app also seeds automatically on startup if the table is empty.
"""
from datetime import datetime, timedelta

import models
from database import Base, SessionLocal, engine

SAMPLE_FEEDBACK = [
    ("Aarav Sharma", "Python Fundamentals Bootcamp", 5,
     "Excellent trainer. The hands-on labs were well-paced and the project at the end tied everything together."),
    ("Priya Iyer", "React Crash Course", 4,
     "Good content, but the section on hooks could use more examples. Loved the live coding."),
    ("Liam O'Connor", "Data Engineering with Spark", 3,
     "Decent overview, but felt rushed in the last module. Needs more time on tuning."),
    ("Mei Lin", "FastAPI Workshop", 5,
     "Best workshop I have attended. The API design discussion was very practical."),
    ("Sai Rathish", "Cloud Foundations on AWS", 4,
     "Clear explanations and the labs worked first time. Would like a deeper dive on networking."),
    ("Ananya Gupta", "SQL for Analytics", 2,
     "Too basic for experienced participants. The slides also had a few typos."),
    ("Rohan Mehta", "Docker & Kubernetes 101", 5,
     "Crystal clear. The Kubernetes troubleshooting examples were gold."),
    ("Sara Ahmed", "Generative AI Primer", 4,
     "Great intro. Wish there were more code-along sessions for prompt engineering."),
    ("Diego Alvarez", "MLOps Foundations", 3,
     "Useful, but the tooling section moved too fast. Slides as references would help."),
    ("Hannah Kim", "Agile Project Management", 5,
     "Engaging facilitator, lots of real-world scenarios. Loved the retrospective workshop."),
    ("Vivek Nair", "Power BI for Business Users", 4,
     "Solid content, examples were relatable. DAX could use one more hour."),
    ("Emily Carter", "Cybersecurity Awareness", 1,
     "Felt like a checkbox course. Mostly slides being read out without discussion."),
    ("Karthik Subramanian", "TypeScript Deep Dive", 5,
     "Best deep-dive I have done on TS generics. Highly recommended for senior devs."),
    ("Olivia Brown", "Communication Skills Workshop", 4,
     "Practical role-plays helped a lot. The session on difficult conversations was excellent."),
    ("Noah Singh", "DevOps Fundamentals", 3,
     "Good baseline coverage. CI/CD section could be modernized with newer tools."),
]


def seed(force: bool = False) -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(models.Feedback).count()
        if existing and not force:
            print(f"Database already has {existing} feedback rows — skipping seed.")
            return 0

        if force:
            db.query(models.Feedback).delete()
            db.commit()

        now = datetime.utcnow()
        for index, (name, program, rating, comments) in enumerate(SAMPLE_FEEDBACK):
            db.add(
                models.Feedback(
                    participant_name=name,
                    program_name=program,
                    rating=rating,
                    comments=comments,
                    # spread submissions across the past two weeks so the list looks realistic
                    submitted_at=now - timedelta(days=index, hours=index * 2),
                )
            )
        db.commit()
        print(f"Seeded {len(SAMPLE_FEEDBACK)} feedback rows.")
        return len(SAMPLE_FEEDBACK)
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    force_flag = "--force" in sys.argv
    seed(force=force_flag)
