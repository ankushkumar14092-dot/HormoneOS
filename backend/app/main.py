from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.routers import datasets, patients, timeline, representation, registry, benchmark
from app.core.config import settings
from app.core.database import get_db
from app.repositories.repos import DatasetRepo, PatientRepo
from app.models.models import Embedding

app = FastAPI(
    title="HormoneOS — Open Research Infrastructure for Women's Hormonal AI",
    version="1.0.0",
    description="Universal Hormonal Schema (UHS) + Hormone State Foundation (HSF) API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    datasets.router,
    patients.router,
    timeline.router,
    representation.router,
    registry.router,
    benchmark.router,
]:
    app.include_router(router)


@app.get("/api/v1/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    n_datasets = len(DatasetRepo(db).list_all())
    n_patients = len(PatientRepo(db).list_all())
    n_embeddings = db.query(Embedding).count()
    return {
        "status": "ok",
        "service": "HormoneOS",
        "n_datasets": n_datasets,
        "n_patients": n_patients,
        "n_embeddings": n_embeddings
    }
