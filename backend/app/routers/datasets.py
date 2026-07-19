from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import os
from app.core.database import get_db
from app.schemas.schemas import IngestRequest, IngestResponse, DatasetOut
from app.services.ingestion import ingest_records
from app.services.dataset_service import upload_dataset, process_dataset_file
from app.repositories.repos import DatasetRepo
from app.core.config import settings

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetOut)
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str        = Form(...),
    version: str     = Form("1.0.0"),
    db: Session      = Depends(get_db),
):
    res = await upload_dataset(db, file, name, version)
    dest = os.path.join(settings.UPLOAD_DIR, file.filename)
    background_tasks.add_task(process_dataset_file, res.id, dest)
    return res


@router.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, db: Session = Depends(get_db)):
    return ingest_records(db, payload.dataset_id, payload.records)


@router.get("/versions")
def versions(name: str, db: Session = Depends(get_db)):
    dataset = DatasetRepo(db).get_by_name(name)
    if not dataset:
        raise HTTPException(404, f"Dataset '{name}' not found")
    return {
        "name":                   dataset.name,
        "version":                dataset.version,
        "sha256_hash":            dataset.sha256_hash,
        "transformation_history": dataset.transformation_history,
        "created_at":             dataset.created_at,
    }


@router.get("/", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return DatasetRepo(db).list_all()
