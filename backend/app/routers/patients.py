from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import PatientCreate, PatientOut
from app.repositories.repos import PatientRepo
import uuid as _uuid

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    repo = PatientRepo(db)
    p = repo.create(
        uuid=str(_uuid.uuid4()),
        birth_year=payload.birth_year,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
    )
    db.commit()
    db.refresh(p)
    return p


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    p = PatientRepo(db).get(patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    return p


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return PatientRepo(db).list_all()
