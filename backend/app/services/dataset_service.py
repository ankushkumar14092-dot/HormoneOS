import hashlib
import os
import shutil
import zipfile
import tempfile
import json
import pandas as pd
from datetime import datetime, timezone
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.repositories.repos import DatasetRepo
from app.schemas.schemas import (
    DatasetCreate, DatasetOut, UHSRecord, CycleInfo,
    WearableData, HormoneData, GlucoseData, SymptomEntry
)
from app.core.config import settings
from app.services.ingestion import ingest_records

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# ── mcPHASES Parsing Helpers ──────────────────────────────────────────────────

PHASE_MAP = {
    "menstrual":  "menstrual",
    "follicular": "follicular",
    "fertility":  "ovulatory",
    "luteal":     "luteal",
}

SYMPTOM_COLS = [
    "appetite", "exerciselevel", "headaches", "cramps",
    "sorebreasts", "fatigue", "sleepissue", "moodswing",
    "stress", "foodcravings", "indigestion", "bloating",
]

SEVERITY_MAP = {
    "very low/little": 1, "low": 2, "moderate": 3, "high": 4, "very high": 5,
}

def _severity(val) -> int:
    if pd.isna(val):
        return 3
    return SEVERITY_MAP.get(str(val).strip().lower(), 3)

def load_daily_mean(path: str, value_col: str, rename: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    if value_col not in df.columns:
        return pd.DataFrame(columns=["id", "day_in_study", rename])
    return df.groupby(["id", "day_in_study"])[value_col].mean().reset_index().rename(columns={value_col: rename})

def build_master(dataset_dir: str) -> pd.DataFrame:
    p = lambda f: os.path.join(dataset_dir, f)
    hormones = pd.read_csv(p("hormones_and_selfreport.csv"))
    hormones.columns = hormones.columns.str.strip().str.lower()
    hormones = hormones.rename(columns={"pdg": "progesterone"})

    hr = load_daily_mean(p("heart_rate.csv"),          "bpm",                    "heart_rate_bpm")
    am_raw = pd.read_csv(p("active_minutes.csv"))
    am_raw.columns = am_raw.columns.str.strip().str.lower()
    am_raw["active_minutes"] = am_raw["lightly"] + am_raw["moderately"] + am_raw["very"]
    am = am_raw.groupby(["id", "day_in_study"])["active_minutes"].sum().reset_index()

    ct_raw = pd.read_csv(p("computed_temperature.csv"))
    ct_raw = ct_raw.rename(columns={"sleep_start_day_in_study": "day_in_study"})
    ct = ct_raw.groupby(["id", "day_in_study"])["nightly_temperature"].mean().reset_index()
    ct = ct.rename(columns={"nightly_temperature": "computed_temperature_c"})

    vo = load_daily_mean(p("demographic_vo2_max.csv"),  "demographic_vo2_max",   "vo2_max")
    ve = load_daily_mean(p("demographic_vo2_max.csv"),  "demographic_vo2_max_error", "vo2_max_error")
    gl = load_daily_mean(p("glucose.csv"),              "glucose_value",         "glucose_mg_dl")
    rhr= load_daily_mean(p("resting_heart_rate.csv"),   "value",                 "resting_hr")

    master = hormones.copy()
    for df in [hr, am, ct, vo, ve, gl, rhr]:
        master = master.merge(df, on=["id", "day_in_study"], how="left")

    subj = pd.read_csv(p("subject-info.csv"), usecols=["id", "birth_year"])
    master = master.merge(subj, on="id", how="left")
    return master

def master_to_uhs(row: pd.Series) -> UHSRecord:
    phase_raw = str(row.get("phase", "unknown")).strip().lower()
    phase     = PHASE_MAP.get(phase_raw, "unknown")
    base_year = int(row.get("study_interval", 2022))
    day       = int(row.get("day_in_study", 1))
    from datetime import timedelta
    ts = datetime(base_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day - 1)

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

# ── NHANES SAS Transport XPT Parser ───────────────────────────────────────────

def parse_xpt_files(file_paths: list[str]) -> list[UHSRecord]:
    dfs = []
    for fp in file_paths:
        try:
            # pandas supports importing SAS xport formats natively
            df = pd.read_sas(fp, format="xport")
            df.columns = df.columns.str.upper()
            dfs.append(df)
        except Exception as e:
            raise Exception(f"Failed to read SAS Transport XPT file {os.path.basename(fp)}: {str(e)}")
            
    if not dfs:
        raise Exception("No valid XPT files found")
        
    master = dfs[0]
    for df in dfs[1:]:
        if 'SEQN' in df.columns and 'SEQN' in master.columns:
            master = master.merge(df, on='SEQN', how='outer')
            
    if 'SEQN' not in master.columns:
        raise Exception("Participant identifier 'SEQN' not found in XPT datasets")
        
    records = []
    for _, row in master.iterrows():
        seqn = int(row['SEQN'])
        
        # Demographics
        age = row.get('RIDAGEYR', None)
        birth_year = int(2026 - age) if pd.notna(age) else None
        weight = row.get('BMXWT', None)
        height = row.get('BMXHT', None)
        
        # Biomarkers
        glucose_val = row.get('LBXGLU', None)
        estrogen = row.get('LBDE2', None)
        progesterone = row.get('LBDP1', None)
        lh = row.get('LBDLH', None)
        fsh = row.get('LBDFSH', None)
        
        # Default timestamp for cross-sectional study
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        uhs_record = UHSRecord(
            patient_id=seqn,
            timestamp=ts,
            day_in_study=1,
            cycle=CycleInfo(cycle_number=1, phase="unknown"),
            wearables=WearableData(
                heart_rate_bpm=None,
                active_minutes=None,
                computed_temperature_c=None
            ),
            hormones=HormoneData(
                estrogen_pg_ml=float(estrogen) if pd.notna(estrogen) else None,
                progesterone_ng_ml=float(progesterone) if pd.notna(progesterone) else None,
                lh_miu_ml=float(lh) if pd.notna(lh) else None,
                fsh_miu_ml=float(fsh) if pd.notna(fsh) else None
            ),
            symptoms=[],
            glucose=GlucoseData(
                glucose_mg_dl=float(glucose_val) if pd.notna(glucose_val) else None
            ),
            birth_year=birth_year,
            weight_kg=float(weight) if pd.notna(weight) else None,
            height_cm=float(height) if pd.notna(height) else None
        )
        records.append(uhs_record)
        
    return records

# ── Background Process Ingestion Task ─────────────────────────────────────────

def process_dataset_file(dataset_id: int, file_path: str):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        repo = DatasetRepo(db)
        dataset = repo.get(dataset_id)
        if not dataset:
            return

        # Start Log
        history = list(dataset.transformation_history or [])
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operator": "system-pipeline",
            "action": "Starting file extraction and UHS validation..."
        })
        dataset.transformation_history = history
        db.commit()

        records = []
        if file_path.endswith(".zip"):
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                # Scan extracted contents
                all_files = []
                for root, dirs, files in os.walk(tmpdir):
                    for f in files:
                        all_files.append(os.path.join(root, f))
                        
                # Check for XPT files
                xpt_files = [f for f in all_files if f.lower().endswith(".xpt")]
                
                if xpt_files:
                    # Ingest as NHANES dataset
                    history = list(dataset.transformation_history or [])
                    history.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "operator": "system-pipeline",
                        "action": f"Found {len(xpt_files)} SAS XPT files. Launching outer-merge compiler on SEQN..."
                    })
                    dataset.transformation_history = history
                    db.commit()
                    records = parse_xpt_files(xpt_files)
                else:
                    # Check for mcPHASES csv files
                    target_dir = tmpdir
                    found = False
                    for root, dirs, files in os.walk(tmpdir):
                        if "subject-info.csv" in files and "hormones_and_selfreport.csv" in files:
                            target_dir = root
                            found = True
                            break
                    
                    if not found:
                        raise Exception("ZIP archive does not contain recognized datasets (expected NHANES XPT or mcPHASES CSV files)")
                    
                    master = build_master(target_dir)
                    for _, row in master.iterrows():
                        records.append(master_to_uhs(row))
                        
        elif file_path.endswith(".xpt"):
            records = parse_xpt_files([file_path])
        elif file_path.endswith(".json"):
            with open(file_path, "r") as f:
                raw_data = json.load(f)
            
            if isinstance(raw_data, dict) and "records" in raw_data:
                raw_records = raw_data["records"]
            elif isinstance(raw_data, list):
                raw_records = raw_data
            else:
                raise Exception("JSON dataset must be a list of records or a dictionary with a 'records' key")
                
            for idx, item in enumerate(raw_records):
                try:
                    records.append(UHSRecord.model_validate(item))
                except Exception as e:
                    raise Exception(f"Validation failed at record index {idx}: {str(e)}")
        else:
            raise Exception("Unsupported file format. Please upload a .zip, .xpt, or .json file.")

        # Ingestion Log
        history = list(dataset.transformation_history or [])
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operator": "system-pipeline",
            "action": f"Valid: {len(records)} records conform to UHS. Beginning database insertion..."
        })
        dataset.transformation_history = history
        db.commit()

        result = ingest_records(db, dataset_id, records)
        
        # Group records by patient_id to trigger representation embeddings generation
        from app.services.hsf_service import generate_representation
        patient_groups = {}
        for r in records:
            patient_groups.setdefault(r.patient_id, []).append(r)
            
        history = list(dataset.transformation_history or [])
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operator": "system-pipeline",
            "action": f"Ingestion Completed. Generating HSF representations for {len(patient_groups)} cohort subjects..."
        })
        dataset.transformation_history = history
        db.commit()

        # Generate representation for each patient sequence (capped at 100 for database performance)
        generated_count = 0
        pids_to_process = list(patient_groups.keys())
        if len(pids_to_process) > 100:
            pids_to_process = pids_to_process[:100]

        for pid in pids_to_process:
            group = patient_groups[pid]
            try:
                generate_representation(db, pid, group)
                generated_count += 1
            except Exception as ge:
                pass

        # Final pipeline completion log
        history = list(dataset.transformation_history or [])
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operator": "system-pipeline",
            "action": f"Pipeline Completed successfully. Ingested={result.inserted} timelines. Generated={generated_count} representations."
        })
        dataset.transformation_history = history
        db.commit()

    except Exception as e:
        db.rollback()
        repo = DatasetRepo(db)
        dataset = repo.get(dataset_id)
        if dataset:
            history = list(dataset.transformation_history or [])
            history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operator": "system-pipeline",
                "action": f"Processing Failed: {str(e)}"
            })
            dataset.transformation_history = history
            db.commit()
    finally:
        db.close()

# ── API Upload Entry ──────────────────────────────────────────────────────────

async def upload_dataset(db: Session, file: UploadFile, name: str, version: str) -> DatasetOut:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(settings.UPLOAD_DIR, file.filename)

    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)

    sha = _sha256(dest)
    repo = DatasetRepo(db)
    existing = repo.get_by_name(name)

    if existing:
        existing.version    = version
        existing.sha256_hash = sha
        existing.transformation_history = [{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operator": "system-uploader",
            "action": f"File uploaded: {file.filename}. Overwriting metadata."
        }]
        db.commit()
        db.refresh(existing)
        return DatasetOut.model_validate(existing)

    dataset = repo.create(
        name=name,
        version=version,
        sha256_hash=sha,
        transformation_history=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operator": "system-uploader",
            "action": f"File uploaded: {file.filename}. Registered metadata."
        }]
    )
    db.commit()
    db.refresh(dataset)
    return DatasetOut.model_validate(dataset)
