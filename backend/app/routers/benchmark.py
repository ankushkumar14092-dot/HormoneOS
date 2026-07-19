from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import BenchmarkRequest, BenchmarkOut
from app.services.benchmark import run_benchmark

router = APIRouter(prefix="/api/v1", tags=["benchmark"])


@router.post("/benchmark", response_model=BenchmarkOut)
def benchmark(payload: BenchmarkRequest, db: Session = Depends(get_db)):
    return run_benchmark(db, payload.task, payload.patient_ids)
