#!/usr/bin/env python3
"""Seed the database with synthetic data for local development."""
import sys, os, uuid, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

from datetime import datetime, timedelta, timezone
import numpy as np
from app.core.database import SessionLocal, engine, Base
from app.models import models  # register all tables
from app.repositories.repos import PatientRepo, DatasetRepo, TimelineRepo, CycleRepo, EmbeddingRepo
from app.models.models import Wearable, Hormone, Glucose

Base.metadata.create_all(bind=engine)

PHASES = ["menstrual", "follicular", "ovulatory", "luteal"]
N_PATIENTS = 5
N_DAYS     = 28


def seed():
    db = SessionLocal()
    try:
        # Dataset
        repo_d  = DatasetRepo(db)
        dataset = repo_d.get_by_name("seed-synthetic")
        if not dataset:
            dataset = repo_d.create("seed-synthetic", "1.0.0", "abc123seed",
                                    [{"timestamp": datetime.now(timezone.utc).isoformat(),
                                      "operator": "seed_db.py", "action": "Synthetic seed"}])
            db.commit()

        repo_p  = PatientRepo(db)
        repo_tl = TimelineRepo(db)
        repo_c  = CycleRepo(db)
        repo_e  = EmbeddingRepo(db)

        for pid in range(1, N_PATIENTS + 1):
            patient = repo_p.create(uuid=str(uuid.uuid4()), birth_year=1990 + pid,
                                    weight_kg=60 + pid, height_cm=165 + pid)
            db.flush()

            for day in range(N_DAYS):
                phase = PHASES[day // 7 % 4]
                cycle = repo_c.get_or_create(patient.id, cycle_number=1, phase=phase)
                ts    = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=day)
                tl    = repo_tl.create(patient.id, dataset.id, ts, day_in_study=day, cycle_id=cycle.id)

                db.add(Wearable(
                    timeline_id=tl.id,
                    heart_rate=60 + random.uniform(-5, 15),
                    active_minutes=random.uniform(20, 90),
                    computed_temperature=36.5 + random.uniform(-0.3, 0.8),
                    vo2_max=35 + random.uniform(-3, 5),
                ))
                db.add(Hormone(
                    timeline_id=tl.id,
                    estrogen=random.uniform(30, 400),
                    progesterone=random.uniform(0.5, 20),
                    lh=random.uniform(2, 80),
                    fsh=random.uniform(2, 15),
                ))
                db.add(Glucose(timeline_id=tl.id, glucose_value=random.uniform(70, 110)))

                # Synthetic 128-d embedding
                vec = np.random.randn(128).astype(np.float32)
                vec /= np.linalg.norm(vec)
                repo_e.create(tl.id, "hsf-v1", vec.tolist())

            db.commit()
            print(f"  Seeded patient {patient.id}")

        print(f"Done. {N_PATIENTS} patients × {N_DAYS} days seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
