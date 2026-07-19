from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.repos import TimelineRepo, PatientRepo
from app.schemas.schemas import (
    TimelineOut, WearableData, HormoneData, SymptomEntry, GlucoseData
)

router = APIRouter(prefix="/api/v1/timeline", tags=["timeline"])


def _serialize(tl) -> TimelineOut:
    w = tl.wearable
    h = tl.hormone
    g = tl.glucose
    return TimelineOut(
        id=tl.id,
        patient_id=tl.patient_id,
        cycle_id=tl.cycle_id,
        dataset_id=tl.dataset_id,
        timestamp=tl.timestamp,
        day_in_study=tl.day_in_study,
        wearables=WearableData(
            heart_rate_bpm=w.heart_rate if w else None,
            active_minutes=w.active_minutes if w else None,
            computed_temperature_c=w.computed_temperature if w else None,
            vo2_max=w.vo2_max if w else None,
            vo2_max_error=w.vo2_max_error if w else None,
        ) if w else None,
        hormones=HormoneData(
            estrogen_pg_ml=h.estrogen if h else None,
            progesterone_ng_ml=h.progesterone if h else None,
            lh_miu_ml=h.lh if h else None,
            fsh_miu_ml=h.fsh if h else None,
        ) if h else None,
        symptoms=[SymptomEntry(name=s.symptom_name, severity=s.severity) for s in tl.symptoms],
        glucose=GlucoseData(glucose_mg_dl=g.glucose_value) if g else None,
    )


@router.get("/{patient_id}", response_model=List[TimelineOut])
def get_timeline(
    patient_id: int,
    start: Optional[datetime] = None,
    end:   Optional[datetime] = None,
    db:    Session            = Depends(get_db),
):
    if not PatientRepo(db).get(patient_id):
        raise HTTPException(404, "Patient not found")
    rows = TimelineRepo(db).get_by_patient(patient_id, start, end)
    return [_serialize(r) for r in rows]
