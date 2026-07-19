#!/usr/bin/env python3
"""
Ingest the real mcPHASES dataset into HormoneOS.

Usage:
    python ingest_mcphases.py --dataset-dir <path_to_mcphases_dir>

All CSV files are joined on (id, day_in_study) to produce one UHS record
per patient per day, then persisted via the ingestion service.
"""
import sys, os, argparse, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

import pandas as pd
import numpy as np
from datetime import datetime, timezone

from app.core.database import SessionLocal, engine, Base
from app.models import models as _models          # register tables
from app.repositories.repos import DatasetRepo
from app.services.ingestion import ingest_records
from app.schemas.schemas import (
    UHSRecord, CycleInfo, WearableData, HormoneData,
    GlucoseData, SymptomEntry,
)

Base.metadata.create_all(bind=engine)

DATASET_NAME = "mcphases-v1.0.0"
DATASET_VER  = "1.0.0"

# mcPHASES phase labels → UHS canonical phases
PHASE_MAP = {
    "menstrual":  "menstrual",
    "follicular": "follicular",
    "fertility":  "ovulatory",
    "luteal":     "luteal",
}

# Symptom columns and their ordinal scale in the dataset
SYMPTOM_COLS = [
    "appetite", "exerciselevel", "headaches", "cramps",
    "sorebreasts", "fatigue", "sleepissue", "moodswing",
    "stress", "foodcravings", "indigestion", "bloating",
]
SEVERITY_MAP = {
    "very low/little": 1, "low": 2, "moderate": 3, "high": 4, "very high": 5,
}


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _severity(val) -> int:
    if pd.isna(val):
        return 3
    return SEVERITY_MAP.get(str(val).strip().lower(), 3)


def load_daily_mean(path: str, value_col: str, rename: str) -> pd.DataFrame:
    """Load a CSV, normalise column names, aggregate to daily mean per patient."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    if value_col not in df.columns:
        return pd.DataFrame(columns=["id", "day_in_study", rename])
    return df.groupby(["id", "day_in_study"])[value_col].mean().reset_index().rename(columns={value_col: rename})


def build_master(dataset_dir: str) -> pd.DataFrame:
    p = lambda f: os.path.join(dataset_dir, f)

    # ── Core anchor: hormones + self-report (one row per patient per day) ──
    hormones = pd.read_csv(p("hormones_and_selfreport.csv"))
    hormones.columns = hormones.columns.str.strip().str.lower()
    hormones = hormones.rename(columns={"pdg": "progesterone"})

    # ── Wearables ──
    hr = load_daily_mean(p("heart_rate.csv"),          "bpm",                    "heart_rate_bpm")
    am_raw = pd.read_csv(p("active_minutes.csv"))
    am_raw.columns = am_raw.columns.str.strip().str.lower()
    am_raw["active_minutes"] = am_raw["lightly"] + am_raw["moderately"] + am_raw["very"]
    am = am_raw.groupby(["id", "day_in_study"])["active_minutes"].sum().reset_index()

    # computed_temperature uses sleep_start_day_in_study as the day key
    ct_raw = pd.read_csv(p("computed_temperature.csv"))
    ct_raw = ct_raw.rename(columns={"sleep_start_day_in_study": "day_in_study"})
    ct = ct_raw.groupby(["id", "day_in_study"])["nightly_temperature"].mean().reset_index()
    ct = ct.rename(columns={"nightly_temperature": "computed_temperature_c"})
    vo = load_daily_mean(p("demographic_vo2_max.csv"),  "demographic_vo2_max",   "vo2_max")
    ve = load_daily_mean(p("demographic_vo2_max.csv"),  "demographic_vo2_max_error", "vo2_max_error")
    gl = load_daily_mean(p("glucose.csv"),              "glucose_value",         "glucose_mg_dl")
    rhr= load_daily_mean(p("resting_heart_rate.csv"),   "value",                 "resting_hr")

    # ── Merge everything onto hormones anchor ──
    master = hormones.copy()
    for df in [hr, am, ct, vo, ve, gl, rhr]:
        master = master.merge(df, on=["id", "day_in_study"], how="left")

    # ── Subject demographics ──
    subj = pd.read_csv(p("subject-info.csv"), usecols=["id", "birth_year"])
    master = master.merge(subj, on="id", how="left")

    return master


def master_to_uhs(row: pd.Series) -> UHSRecord:
    phase_raw = str(row.get("phase", "unknown")).strip().lower()
    phase     = PHASE_MAP.get(phase_raw, "unknown")

    # Build timestamp: 2022-01-01 + day_in_study days
    base_year = int(row.get("study_interval", 2022))
    day       = int(row.get("day_in_study", 1))
    from datetime import timedelta
    ts = datetime(base_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day - 1)

    # Symptoms
    symptoms = []
    for col in SYMPTOM_COLS:
        val = row.get(col)
        if pd.notna(val):
            symptoms.append(SymptomEntry(name=col, severity=_severity(val)))

    def _f(col):
        v = row.get(col)
        return float(v) if pd.notna(v) else None

    return UHSRecord(
        patient_id=int(row["id"]),
        timestamp=ts,
        day_in_study=day,
        cycle=CycleInfo(cycle_number=1, phase=phase),
        wearables=WearableData(
            heart_rate_bpm=_f("heart_rate_bpm"),
            active_minutes=_f("active_minutes"),
            computed_temperature_c=_f("computed_temperature_c"),
            vo2_max=_f("vo2_max"),
            vo2_max_error=_f("vo2_max_error"),
        ),
        hormones=HormoneData(
            estrogen_pg_ml=_f("estrogen"),
            progesterone_ng_ml=_f("progesterone"),
            lh_miu_ml=_f("lh"),
            fsh_miu_ml=None,
        ),
        symptoms=symptoms,
        glucose=GlucoseData(glucose_mg_dl=_f("glucose_mg_dl")),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        default="/Users/ankushkumarguptapahleja/Downloads/HARMONEOS/"
                "mcphases-a-dataset-of-physiological-hormonal-and-self-reported-events-and-symptoms-for-menstrual-health-tracking-with-wearables-1.0.0",
    )
    args = parser.parse_args()

    print(f"Building master table from {args.dataset_dir} …")
    master = build_master(args.dataset_dir)
    print(f"  {len(master)} daily rows across {master['id'].nunique()} patients")

    sha = _sha256(os.path.join(args.dataset_dir, "hormones_and_selfreport.csv"))

    db = SessionLocal()
    try:
        repo    = DatasetRepo(db)
        dataset = repo.get_by_name(DATASET_NAME)
        if not dataset:
            dataset = repo.create(
                name=DATASET_NAME,
                version=DATASET_VER,
                sha256_hash=sha,
                transformation_history=[{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "operator":  "ingest_mcphases.py",
                    "action":    "Initial ingest: joined heart_rate, active_minutes, "
                                 "computed_temperature, vo2_max, glucose, hormones_and_selfreport",
                }],
            )
            db.commit()
            print(f"  Registered dataset id={dataset.id}  sha256={sha[:16]}…")
        else:
            print(f"  Dataset already registered id={dataset.id}, re-ingesting records…")

        records = [master_to_uhs(row) for _, row in master.iterrows()]
        print(f"  Ingesting {len(records)} UHS records …")
        result = ingest_records(db, dataset.id, records)
        print(f"  ✓ inserted={result.inserted}  skipped={result.skipped}  errors={len(result.errors)}")
        if result.errors:
            for e in result.errors[:10]:
                print(f"    {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
