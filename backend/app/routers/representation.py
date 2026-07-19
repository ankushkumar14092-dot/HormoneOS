from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import (
    RepresentationRequest, RepresentationOut,
    CompareRequest, CompareOut,
    ExplainRequest, ExplainOut,
)
from app.services.hsf_service import generate_representation, explain_representation
from app.services.comparison import compare_patients

router = APIRouter(prefix="/api/v1/representation", tags=["representation"])


@router.post("", response_model=RepresentationOut)
def create_representation(payload: RepresentationRequest, db: Session = Depends(get_db)):
    return generate_representation(db, payload.patient_id, payload.records)


@router.post("/compare", response_model=CompareOut)
def compare(payload: CompareRequest, db: Session = Depends(get_db)):
    return compare_patients(db, payload.patient_a_id, payload.patient_b_id)


@router.post("/explain", response_model=ExplainOut)
def explain(payload: ExplainRequest, db: Session = Depends(get_db)):
    return explain_representation(payload.patient_id, payload.records)
