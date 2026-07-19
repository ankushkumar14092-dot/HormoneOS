#!/usr/bin/env python3
"""
Usage:
    python ingest_dataset.py --csv datasets/mcphases/sample.csv --name mcphases-v1 --version 1.0.0
"""
import argparse, hashlib, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

import pandas as pd
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.repositories.repos import DatasetRepo
from app.services.ingestion import ingest_records
from app.schemas.schemas import (
    UHSRecord, CycleInfo, WearableData, HormoneData, GlucoseData, SymptomEntry
)


PHASE_ALIASES = {
    "menstrual": "menstrual", "follicular": "follicular",
    "ovulatory": "ovulatory", "luteal": "luteal",
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def row_to_uhs(row: pd.Series) -> UHSRecord:
    phase = PHASE_ALIASES.get(str(row.get("phase", "unknown")).lower(), "unknown")
    ts    = pd.to_datetime(row.get("timestamp", row.get("date", datetime.now(timezone.utc))))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return UHSRecord(
        patient_id=int(row.get("patient_id", row.get("subject_id", 0))),
        timestamp=ts,
        day_in_study=int(row["day_in_study"]) if "day_in_study" in row and pd.notna(row["day_in_study"]) else None,
        cycle=CycleInfo(
            cycle_number=int(row["cycle_number"]) if "cycle_number" in row and pd.notna(row["cycle_number"]) else 1,
            phase=phase,
        ),
        wearables=WearableData(
            heart_rate_bpm=float(row["heart_rate"]) if "heart_rate" in row and pd.notna(row["heart_rate"]) else None,
            active_minutes=float(row["active_minutes"]) if "active_minutes" in row and pd.notna(row["active_minutes"]) else None,
            computed_temperature_c=float(row["computed_temperature"]) if "computed_temperature" in row and pd.notna(row["computed_temperature"]) else None,
            vo2_max=float(row["vo2_max"]) if "vo2_max" in row and pd.notna(row["vo2_max"]) else None,
            vo2_max_error=float(row["vo2_max_error"]) if "vo2_max_error" in row and pd.notna(row["vo2_max_error"]) else None,
        ),
        hormones=HormoneData(
            estrogen_pg_ml=float(row["estrogen"]) if "estrogen" in row and pd.notna(row["estrogen"]) else None,
            progesterone_ng_ml=float(row["progesterone"]) if "progesterone" in row and pd.notna(row["progesterone"]) else None,
            lh_miu_ml=float(row["lh"]) if "lh" in row and pd.notna(row["lh"]) else None,
            fsh_miu_ml=float(row["fsh"]) if "fsh" in row and pd.notna(row["fsh"]) else None,
        ),
        glucose=GlucoseData(
            glucose_mg_dl=float(row["glucose"]) if "glucose" in row and pd.notna(row["glucose"]) else None,
        ),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv",     required=True)
    parser.add_argument("--name",    required=True)
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()

    sha = sha256_file(args.csv)
    df  = pd.read_csv(args.csv)
    print(f"Loaded {len(df)} rows from {args.csv}  sha256={sha[:12]}…")

    db = SessionLocal()
    try:
        repo    = DatasetRepo(db)
        dataset = repo.get_by_name(args.name)
        if not dataset:
            dataset = repo.create(name=args.name, version=args.version, sha256_hash=sha,
                                  transformation_history=[{
                                      "timestamp": datetime.now(timezone.utc).isoformat(),
                                      "operator": "ingest_dataset.py",
                                      "action": f"Initial ingest from {args.csv}",
                                  }])
            db.commit()

        records = [row_to_uhs(row) for _, row in df.iterrows()]
        result  = ingest_records(db, dataset.id, records)
        print(f"Inserted={result.inserted}  Skipped={result.skipped}  Errors={len(result.errors)}")
        if result.errors:
            for e in result.errors[:5]:
                print(" ", e)
    finally:
        db.close()


if __name__ == "__main__":
    main()
